import sqlite3
import shutil
from typing import List, Dict, Optional, Tuple
import os
import subprocess

# Text extraction
import docx2txt
import fitz  # PyMuPDF
from pypdf import PdfReader

def _fetch_files(conn: sqlite3.Connection, user_id: int, project_name: str, only_text: bool = False) -> List[Dict[str, str]]:
    """
    Fetch files for a project from the 'files' table.
    Returns: [{'file_name','file_type','file_path'}, ...]
    """
    query = """
        SELECT file_name, file_type, file_path
        FROM files
        WHERE user_id = ? AND project_name = ?
    """
    params = [user_id, project_name]
    if only_text:
        query += " AND file_type = 'text'"

    rows = conn.execute(query, params).fetchall()
    return [{"file_name": r[0], "file_type": r[1], "file_path": r[2]} for r in rows]

def zip_paths(zip_path: str) -> Tuple[str, str, str]:
    """
    Returns (zip_data_dir, zip_name, base_path)
    - zip_data_dir: absolute path to ./zip_data
    - zip_name:     the uploaded zip filename (no extension)
    - base_path:    ./zip_data/<zip_name>
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_data_dir = os.path.join(repo_root, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(zip_data_dir, zip_name)
    return zip_data_dir, zip_name, base_path

def cleanup_extracted_zip(zip_path: str) -> None:
    """
    Remove the entire ./zip_data workspace created for a ZIP upload.
    Safe to call multiple times; silently skips missing paths.
    """
    if not zip_path:
        return

    try:
        zip_data_dir, _, _ = zip_paths(zip_path)
    except Exception:
        return

    if os.path.isdir(zip_data_dir):
        try:
            shutil.rmtree(zip_data_dir)
            print(f"\nCleaned up extracted files at: {zip_data_dir}")
        except OSError as exc:
            print(f"\nWarning: Could not remove extracted files at {zip_data_dir}: {exc}")

def ensure_table(conn: sqlite3.Connection, table: str, ddl: str) -> None:
    conn.execute(ddl)
    conn.commit()

def is_git_repo(path: str) -> bool:
    """
    A directory is a repo if it contains a .git FOLDER,
    or a .git FILE (worktree) pointing to another gitdir.
    """
    git_dir = os.path.join(path, ".git")
    if os.path.isdir(git_dir):
        return True
    if os.path.isfile(git_dir):
        try:
            with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                return "gitdir:" in f.read().lower()
        except Exception:
            return False
    return False

def bfs_find_repo(root: str, max_depth: int = 2) -> Optional[str]:
    """
    Breadth-first search to find a nested repo under root, up to max_depth.
    Returns the first directory containing .git.
    """
    if not os.path.isdir(root):
        return None
    if is_git_repo(root):
        return root
    queue: List[Tuple[str, int]] = [(root, 0)]
    while queue:
        path, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            entries = [os.path.join(path, ent) for ent in os.listdir(path)]
        except Exception:
            continue
        for p in entries:
            if os.path.isdir(p):
                if is_git_repo(p):
                    return p
                if depth < max_depth:
                    queue.append((p, depth + 1))
    return None


## Text Extraction

SUPPORTED_TEXT_EXTENSIONS={'.txt', '.pdf','.docx'}

def extract_text_file(filepath: str)->Optional[str]: #extract text
    extension=os.path.splitext(filepath)[1].lower()
    if(extension) not in SUPPORTED_TEXT_EXTENSIONS:
        return None
    
    try:
        if extension=='.txt':
            return extractfromtxt(filepath)
        elif extension == '.pdf':
            return extractfrompdf(filepath)
        elif extension == '.docx':
            return extractfromdocx(filepath)
    except Exception as e:
        return None  
    return None

def extractfromtxt(filepath:str)->str:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extractfrompdf(filepath:str)->str:
    text=[]
    try:
        pdf=fitz.open(filepath)
        for page in pdf:
            text.append(page.get_text())
        pdf.close()
        return '\n'.join(text)
    except Exception as e:
        print(f"Error: {e}")
        return ""

def extractfromdocx (filepath: str)->str:
    try:
        text=docx2txt.process(filepath)
        if text:
            return text
    except Exception as e:
        print(f"Error : {e}")
        
        

## Code extraction

SUPPORTED_CODE_EXTENSIONS={'.py', '.java', '.js', '.html', '.css', '.c', '.cpp', '.h'}

def extract_code_file(filepath: str)->Optional[str]:
    root, extension = os.path.splitext(filepath)
    if extension.lower() not in SUPPORTED_CODE_EXTENSIONS:
        return None
    
    try:
        # .py, .java, .js, .html, .css, .c, .cpp, .h can be accessed using regular text extraction
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        # instead of extracting the whole code, we just need function names, class headers, comments, and docstrings
        context_lines = []
        for line in lines:
            stripped = line.strip()
            # python, c, c++, java
            if stripped.startswith(("def ", "class ", "#", "//", "/*", "*", '"""', "'''")):
                context_lines.append(line.rstrip())
            # html, css, js comments or tags
            elif stripped.startswith(("<!--", "<!DOCTYPE", "<html", "<head", "<body", "<script", "<style")):
                context_lines.append(line.rstrip())
                
        return "\n".join(line for line in context_lines if line.strip()) if context_lines else None
    
    except Exception as e:
        print(f"Error extracting code from {filepath}: {e}")
        return None
    return None

def extract_readme_file(base_path: str) -> Optional[str]:
    for filename in os.listdir(base_path):
        if filename.lower().startswith("readme") and filename.lower().endswith((".md", ".txt")):
            filepath = os.path.join(base_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading README: {e}")
                return None
    return None
