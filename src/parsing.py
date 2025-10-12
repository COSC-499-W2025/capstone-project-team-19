import os
import zipfile
import time
import json

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
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        if len(zip_ref.namelist()) == 0:
            return []

        extract_to = "../zip_data/parsed_zip_rawdata"
        zip_ref.extractall(extract_to)

    files_info = collect_file_info(extract_to)

    # Write to JSON file
    output_path = "../zip_data/parsed_zip_metadata.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(files_info, f, indent=4)

    print (f"Parsed file info has been saved to {output_path}")
    #print("Extracted file info:")
    #for f in files_info:
        #print(f)

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

