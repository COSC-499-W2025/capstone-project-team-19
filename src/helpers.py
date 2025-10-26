import sqlite3
from typing import List, Dict, Optional
import os

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
        
        
