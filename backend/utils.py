import os
from backend.agents.context_builder import RelevantFiles

def get_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f""

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
