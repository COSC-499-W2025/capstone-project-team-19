import sqlite3
import shutil
from typing import List, Dict, Optional, Tuple
import os
import subprocess
import pandas as pd
import re

# Text extraction
import docx2txt
import fitz  # PyMuPDF
from pypdf import PdfReader
try:
    from src import constants
except ModuleNotFoundError:
    import constants

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
def get_file_extension_from_db(conn: sqlite3.Connection, user_id: int, filepath: str) -> str | None:
    """Fetch file extension from DB using normalized relative path matching."""
    try:
        # Normalize absolute → relative path (so it matches DB file_path entries)
        base_path = os.path.join(os.path.dirname(__file__), "..", "zip_data")
        rel_path = os.path.relpath(filepath, base_path).replace("\\", "/")

        # Remove any accidental leading "zip_data/" or "./"
        if rel_path.startswith("zip_data/"):
            rel_path = rel_path[len("zip_data/"):]
        if rel_path.startswith("./"):
            rel_path = rel_path[2:]

        # --- Main lookup ---
        cur = conn.cursor()
        cur.execute(
            "SELECT extension FROM files WHERE user_id = ? AND file_path = ?",
            (user_id, rel_path),
        )
        result = cur.fetchone()

        # --- Fallback lookup (e.g., partial match if path separators differ) ---
        if not result:
            cur.execute(
                "SELECT extension FROM files WHERE user_id = ? AND file_path LIKE ?",
                (user_id, f"%{os.path.basename(filepath)}%"),
            )
            result = cur.fetchone()

        return result[0] if result else None

    except Exception as e:
        print(f"DB lookup failed for {filepath}: {e}")
        return None


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
        # Point cleanup to ./src/analysis/zip_data instead of ./src/zip_data
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zip_data_dir = os.path.join(repo_root, "analysis", "zip_data")
    except Exception:
        return

    if os.path.isdir(zip_data_dir):
        try:
            shutil.rmtree(zip_data_dir)
            if constants.VERBOSE:
                print(f"\nCleaned up extracted files at: {zip_data_dir}")
        except OSError as exc:
            if constants.VERBOSE:
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

## Text Extraction

def extract_text_file(filepath: str, conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    # Skip DB lookup if conn or user_id not provided
    if conn is None or user_id is None:
        # fallback: infer from file extension
        extension = os.path.splitext(filepath)[1].lower()
    else:
        extension = get_file_extension_from_db(conn, user_id, filepath)

    if not extension:
        print(f"Warning: No extension found in DB for {filepath}, skipping.")
        return None
    
    try:
        match extension:
            case '.txt' | '.md':
                return extractfromtxt(filepath)
            case '.pdf':
                return extractfrompdf(filepath)
            case '.docx':
                return extractfromdocx(filepath)
            case '.csv':
                return extractfromcsv(filepath)
            case _:
                print(f"Unsupported text extension '{extension}' for {filepath}")
                return None
    except Exception as e:
        print(f"Error extracting from {filepath}: {e}")
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
        

def extractfromcsv(filepath: str, sample_rows: int = 5) -> dict:
    try:
        df = pd.read_csv(filepath, nrows=sample_rows)
        full_df = pd.read_csv(filepath)
        total_rows = len(full_df)
        total_cols = len(full_df.columns)
        null_ratio = (full_df.isnull().sum().sum() / (total_rows * total_cols)) * 100
        dtypes = full_df.dtypes.astype(str).to_dict()
        headers = list(full_df.columns)

        #extracts the column headers, data types, sample rows, total rows, total columns, and missing value percentage
        return {
            "filename": os.path.basename(filepath),
            "headers": headers,
            "dtypes": dtypes,
            "sample_rows": df.head(sample_rows).to_dict(orient="records"),
            "row_count": total_rows,
            "col_count": total_cols,
            "missing_pct": round(null_ratio, 2),
        }
    except Exception as e:
        print(f"Error reading CSV {filepath}: {e}")
        return None

        

## Code extraction

SUPPORTED_CODE_EXTENSIONS={'.py', '.java', '.js', '.html', '.css', '.c', '.cpp', '.h'}

def read_file_content(filepath: str) -> Optional[str]:
    """
    Read the full contents of a file.
    Used for skill detection where we need complete file analysis.

    Args:
        filepath: Absolute path to the file

    Returns:
        File contents as string, or None if error
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None


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
    """
    Look for a README*.md / README*.txt anywhere under base_path.
    Prefer the first one we find.
    """
    if not base_path or not os.path.isdir(base_path):
        return None

    try:
        # Walk the tree so zipped repos like with_git/.../capstone-project-team-19/README.md are found
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                lower = filename.lower()
                if lower.startswith("readme") and lower.endswith((".md", ".txt")):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            return f.read()
                    except Exception as e:
                        print(f"Error reading README: {e}")
                        return None
    except Exception as e:
        print(f"Error scanning for README under {base_path}: {e}")
        return None

    return None


SECTION_HEADERS = [
    "abstract", "introduction", "background", "methods", "methodology",
    "results", "results and discussion", "discussion", "conclusion",
    "references", "keywords"
]

def normalize_pdf_paragraphs(text: str):
    """
    Reconstructs paragraphs from messy PDF-extracted text.
    - Rejoins broken lines.
    - Detects standard academic headers.
    - Splits paragraphs cleanly.
    """

    # Remove double/triple newlines
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    paragraphs = []
    current = []

    def is_header(line):
        low = line.lower().rstrip(":")
        return any(low.startswith(h) for h in SECTION_HEADERS)

    for line in lines:
        # New section header → commit previous paragraph
        if is_header(line):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            current.append(line)  # header itself becomes a new paragraph start
            continue

        # Normal continuation → append to the current paragraph
        current.append(line)

    # Final paragraph
    if current:
        paragraphs.append(" ".join(current).strip())

    return paragraphs

