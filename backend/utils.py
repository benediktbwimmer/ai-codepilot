import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from backend.models.shared import RelevantFiles
from typing import List, Dict, Optional, Any
import time
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import logging
import glob
import json
from backend.agents.models import CodeChunkUpdate
import threading
import backoff

logger = logging.getLogger(__name__)

# Cache for index
_index_cache = None
_last_index_update = 0
_INDEX_CACHE_TTL = 300  # 5 minutes
_index_lock = threading.Lock()

def _get_gitignore_spec(root_directory: str) -> PathSpec:
    """Build a PathSpec from all .gitignore files in the directory tree."""
    gitignore_patterns = []
    
    # Walk up the directory tree looking for .gitignore files
    current_dir = root_directory
    while True:
        gitignore_path = os.path.join(current_dir, '.gitignore')
        if os.path.isfile(gitignore_path):
            try:
                with open(gitignore_path, 'r') as f:
                    patterns = f.readlines()
                    gitignore_patterns.extend(p.strip() for p in patterns if p.strip() and not p.startswith('#'))
            except:
                pass
                
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
        current_dir = parent_dir
        
    return PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Splits the text into chunks with specified overlap."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # move start forward with overlap
    return chunks

class SearchIndex:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SearchIndex, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                self.client = chromadb.EphemeralClient(Settings(anonymized_telemetry=False))
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                self._create_collection()
                self._initialized = True
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def _create_collection(self):
        try:
            self.collection = self.client.create_collection(
                name='code_documents',
                embedding_function=self.embedding_function
            )
        except Exception as e:
            logger.warning(f"Failed to create collection: {e}")
            # If collection exists, try getting it
            try:
                self.collection = self.client.get_collection(
                    name='code_documents',
                    embedding_function=self.embedding_function
                )
            except Exception as inner_e:
                logger.error(f"Could not create or get collection: {inner_e}")
                raise
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def add_file(self, filepath: str, content: str, chunk_size: int = 500, overlap: int = 100):
        chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filepath}::chunk{i}"
            try:
                self.collection.add(documents=[chunk], ids=[chunk_id])
            except Exception as e:
                logger.warning(f"Failed to add chunk {i} of {filepath}: {e}")
                raise

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def query(self, query_text: str, n_results: int = 10):
        return self.collection.query(query_texts=[query_text], n_results=n_results)

def get_file_content(file_path: str, root_directory: str = None) -> str:
    """Get the content of a file, ensuring absolute paths are used.
    
    Args:
        file_path: The path to the file to read
        root_directory: The root directory to resolve relative paths against. If None, uses current directory.
    """
    # Convert to absolute path if relative
    if not os.path.isabs(file_path):
        if root_directory:
            file_path = os.path.join(root_directory, file_path)
        else:
            file_path = os.path.join(os.getcwd(), file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return ""

def _build_search_index(root_directory: str) -> SearchIndex:
    index = SearchIndex()
    gitignore_spec = _get_gitignore_spec(root_directory)
    
    for root, dirs, files in os.walk(root_directory):
        # Filter out ignored directories to skip them entirely
        dirs[:] = [d for d in dirs if not gitignore_spec.match_file(os.path.join(root, d))]
        
        for file in files:
            if not file.endswith(('.py', '.js', '.ts', '.svelte', '.html', '.css')):
                continue
            
            file_path = os.path.join(root, file)
            # Skip files that match gitignore patterns
            if gitignore_spec.match_file(file_path):
                continue
            
            content = get_file_content(file_path, root_directory)
            index.add_file(file_path, content)
    
    return index

def _get_or_build_index(root_directory: str) -> SearchIndex:
    global _index_cache, _last_index_update
    
    current_time = time.time()
    if _index_cache is None or (current_time - _last_index_update) > _INDEX_CACHE_TTL:
        _index_cache = _build_search_index(root_directory)
        _last_index_update = current_time
    
    return _index_cache

def get_relevant_snippets(search_terms: str, root_directory: str, top_k: int = 10) -> List[Dict[str, str]]:
    """Searches through files in the codebase for search_terms using ChromaDB."""
    with _index_lock:
        index = _get_or_build_index(root_directory)
        try:
            results = index.query(query_text=search_terms, n_results=top_k)
            snippets = []
            for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
                snippet = {
                    "filename": doc_id.split("::")[0],
                    "snippet": get_file_content(doc_id.split("::")[0], root_directory),  # Get content of the full file
                    "distance": distance
                }
                snippets.append(snippet)
            return snippets
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

def build_full_context(repo_map: str, files: RelevantFiles, root_directory: str = None) -> str:
    """
    Given a repo_map (as a string) and a list of file objects (each with a 'filename' key),
    read the contents of each file and concatenate them with the repo_map.
    
    Args:
        repo_map: A string containing the repository map
        files: RelevantFiles object containing the files to include
        root_directory: The root directory to resolve relative paths against
    """
    context_parts = [f"Repository Map:\n{repo_map}\n"]
    for file in files.files:
        filename = file.filename
        if not os.path.isabs(filename) and root_directory:
            filename = os.path.join(root_directory, filename)
        if filename and os.path.isfile(filename):
            content = get_file_content(filename, root_directory)
            context_parts.append(f"File: {filename}\n{content}\n")
        else:
            context_parts.append(f"File: {filename} not found.\n")
    return "\n".join(context_parts)
