import os
import zipfile
import time
import json

CURR_DIR = os.path.dirname(os.path.abspath(__file__)) # Gives the location of the script itself, not where user is running the command from
REPO_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..")) # Moves up one level into main repository directory

ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
RAWDATA_DIR = os.path.join(ZIP_DATA_DIR, "parsed_zip_rawdata")
METADATA_PATH = os.path.join(ZIP_DATA_DIR, "parsed_zip_metadata.json")

def parse_zip_file(zip_path):
    zip_path = str(zip_path)

    if not os.path.exists(zip_path):
        print(f"Error: The file at {zip_path} does not exist.")
        return
    
    if not zip_path.lower().endswith(".zip"):
        print(f"Error: The provided file is not a ZIP file.")
        return
    
    if not zipfile.is_zipfile(zip_path):
        print(f"Error: The file is not a valid ZIP archive.")
        return
    
    # Make sure directories exist
    os.makedirs(RAWDATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        if len(zip_ref.namelist()) == 0:
            return []

        zip_ref.extractall(RAWDATA_DIR)

    files_info = collect_file_info(RAWDATA_DIR)

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(files_info, f, indent=4)

    print (f"Extracted ZIP to: {RAWDATA_DIR}")
    print(f"Metdata has been saved to: {METADATA_PATH}")

    return files_info


TEXT_EXTENSIONS = {".txt", ".csv", ".docx", ".pdf", ".xlsx"}
CODE_EXTENSIONS = {".py", ".java", ".js", ".html", ".css", ".c", ".cpp", ".h"}

def classify_file(extension: str) -> str:
    if extension in TEXT_EXTENSIONS:
        return "text"
    elif extension in CODE_EXTENSIONS:
        return "code"
    else:
        return "other"

def collect_file_info(root_dir):
    collected = []

    for folder, _, files in os.walk(root_dir):
        # Skip any mac files
        if "__MACOSX" in folder:
            continue

        for file in files:
            full_path = os.path.join(folder, file)
            stats = os.stat(full_path)
            extension = os.path.splitext(file)[1].lower()

            collected.append({
                "file_path": os.path.relpath(full_path, root_dir),
                "file_name": file,
                "extension": extension,
                "file_type": classify_file(extension),
                "size_bytes": stats.st_size,
                "created": time.ctime(stats.st_ctime),
                "modified": time.ctime(stats.st_mtime)
            })
    return collected

