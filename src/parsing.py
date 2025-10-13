import os
import zipfile
import time
import json
import mimetypes

import warnings
warnings.filterwarnings("ignore", message="Duplicate name:")
# This is just to silence the warning in unit test (system doesn't know that we purposefully created a duplicate file for testing)

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
        names = zip_ref.namelist()
        if len(names) == 0:
            return []
        
        seen = {}
        duplicate_names = []
        for name in names:
            if name.endswith("/"):
                continue
            
            info = zip_ref.getinfo(name)
            filename = os.path.basename(name)
            size = info.file_size
            
            key = (filename, size)
            if key in seen:
                print(f"Duplicate found in ZIP: {name}")
                duplicate_names.append(name)
            else:
                seen[key] = True

        if duplicate_names:
            with open(DUPLICATE_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(duplicate_names, f, indent=4)
            print(f"Duplicate files logged at: {DUPLICATE_LOG_PATH}")

        zip_ref.extractall(RAWDATA_DIR)

    files_info = collect_file_info(RAWDATA_DIR)

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(files_info, f, indent=4)

    print (f"Extracted ZIP to: {RAWDATA_DIR}")
    print(f"Metdata has been saved to: {METADATA_PATH}")

    return files_info


TEXT_EXTENSIONS = {".txt", ".csv", ".docx", ".pdf", ".xlsx"}
CODE_EXTENSIONS = {".py", ".java", ".js", ".html", ".css", ".c", ".cpp", ".h"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS.union(CODE_EXTENSIONS)
UNSUPPORTED_LOG_PATH = os.path.join(ZIP_DATA_DIR, "unsupported_files.json")
DUPLICATE_LOG_PATH = os.path.join(ZIP_DATA_DIR, "duplicate_files.json")

def classify_file(extension: str) -> str:
    if extension in TEXT_EXTENSIONS:
        return "text"
    elif extension in CODE_EXTENSIONS:
        return "code"
    else:
        return "other"

def is_valid_mime(file_path, extension):
    mime, _ = mimetypes.guess_type(file_path)
    if not mime:
        return extension in SUPPORTED_EXTENSIONS # trust extensions instead
    
    # Text formats
    if extension in TEXT_EXTENSIONS:
        valid_text_mimes = {
            "text/plain",
            "text/csv",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return mime.startswith("text") or mime in valid_text_mimes

    # Code formats
    if extension in CODE_EXTENSIONS:
        valid_code_mimes = {
            "text/x-python",
            "text/x-c",
            "text/x-c++",
            "text/x-java-source",
            "application/javascript",
            "text/javascript",
            "text/html",
            "text/css",
        }
        return mime.startswith("text") or mime in valid_code_mimes
    return False

def collect_file_info(root_dir):
    collected = []
    unsupported_files = []
    duplicate_files = []
    seen = set()

    for folder, _, files in os.walk(root_dir):
        # Skip any mac files
        if "__MACOSX" in folder:
            continue

        for file in files:
            full_path = os.path.join(folder, file)
            extension = os.path.splitext(file)[1].lower()    

            if extension not in SUPPORTED_EXTENSIONS or not is_valid_mime(full_path, extension):
                print(f"Unsupported file skipped: {file}")
                unsupported_files.append(file)
                continue
            
            stats = os.stat(full_path)

            collected.append({
                "file_path": os.path.relpath(full_path, root_dir),
                "file_name": file,
                "extension": extension,
                "file_type": classify_file(extension),
                "size_bytes": stats.st_size,
                "created": time.ctime(stats.st_ctime),
                "modified": time.ctime(stats.st_mtime)
            })
            
    # Log the unsupported files (feedback to users)
    if unsupported_files:
        with open(UNSUPPORTED_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(unsupported_files, f, indent=4)
        print(f"Unsupported files logged at: {UNSUPPORTED_LOG_PATH}")
    
    if duplicate_files:
        with open(DUPLICATE_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(duplicate_files, f, indent=4)
        print(f"Duplicate files logged at: {DUPLICATE_LOG_PATH}")
    
    return collected

