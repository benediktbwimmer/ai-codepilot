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

logger = logging.getLogger(__name__)

# Cache for file contents and index
_file_content_cache = {}
_index_cache = None
_last_index_update = 0
_INDEX_CACHE_TTL = 300  # 5 minutes

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
    def __init__(self):
        self.client = chromadb.EphemeralClient()
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.create_collection(name='code_documents', embedding_function=self.embedding_function)
    
    def add_file(self, filepath: str, content: str, chunk_size: int = 500, overlap: int = 100):
        chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        for i, chunk in enumerate(chunks):
            # Create a unique id for each chunk
            chunk_id = f"{filepath}::chunk{i}"
            self.collection.add(documents=[chunk], ids=[chunk_id])
    
    def build_index(self):
        # ChromaDB builds the index on the fly, so no action is needed here
        pass


def get_file_content(file_path: str) -> str:
    global _file_content_cache
    
    if file_path in _file_content_cache:
        return _file_content_cache[file_path]
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            _file_content_cache[file_path] = content
            return content
    except Exception as e:
        _file_content_cache[file_path] = ""
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
            
            content = get_file_content(file_path)
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
    index = _get_or_build_index(root_directory)
    results = index.collection.query(query_texts=[search_terms], n_results=top_k)
    snippets = []
    for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
        snippet = {
            "filename": doc_id.split("::")[0],
            "snippet": get_file_content(doc_id),
            "distance": distance
        }
        snippets.append(snippet)
    return snippets

def build_full_context(repo_map: str, files: RelevantFiles) -> str:
    """
    Given a repo_map (as a string) and a list of file objects (each with a 'filename' key),
    read the contents of each file and concatenate them with the repo_map.
    """
    context_parts = [f"Repository Map:\n{repo_map}\n"]
    for file in files.files:
        filename = file.filename
        if filename and os.path.isfile(filename):
            content = get_file_content(filename)
            context_parts.append(f"File: {filename}\n{content}\n")
        else:
            context_parts.append(f"File: {filename} not found.\n")
    return "\n".join(context_parts)
