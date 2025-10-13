import os
import zipfile
from pathlib import Path
import pytest
import json

from parsing import parse_zip_file, collect_file_info, UNSUPPORTED_LOG_PATH, DUPLICATE_LOG_PATH

# Helper
def create_sample_zip_with_various_types(tmp_dir):
    # Creates a sample ZIP file containing text and code files of all supported types

    zip_path = os.path.join(tmp_dir, "mixed_types.zip")
    temp_content_dir = Path(tmp_dir) / "sample_content"
    temp_content_dir.mkdir(exist_ok=True)

    # Text files
    (temp_content_dir / "file.txt").write_text("Hello text file")
    (temp_content_dir / "file.csv").write_text("col1,col2\n1,2\n")
    (temp_content_dir / "file.docx").write_text("This is a DOCX file")
    (temp_content_dir / "file.pdf").write_text("This is a PDF file")
    
    # Code files
    (temp_content_dir / "script.py").write_text("print('hello')")
    (temp_content_dir / "Program.java").write_text("public class Program {}")
    (temp_content_dir / "main.js").write_text("console.log('hi');")
    (temp_content_dir / "index.html").write_text("<!DOCTYPE html><html></html>")
    (temp_content_dir / "styles.css").write_text("body { background: white; }")
    (temp_content_dir / "program.c").write_text("int main() { return 0; }")
    (temp_content_dir / "program.cpp").write_text("#include <iostream>\nint main() { return 0; }")
    (temp_content_dir / "program.h").write_text("#ifndef PROGRAM_H\n#define PROGRAM_H\n#endif")

    # ZIP with nested structure
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in temp_content_dir.iterdir():
            ext = file.suffix.lower()
            if ext in {".py", ".java", ".js", ".html", ".css", ".c", ".cpp", ".h"}:
                arcname = f"code/{file.name}"
            elif ext in {".txt", ".csv", ".docx", ".pdf"}:
                arcname = f"text/{file.name}"
            else:
                arcname = f"misc/{file.name}"
            zipf.write(file, arcname=arcname)

    return zip_path


# Tests
def test_parse_zip_file_handles_all_supported_types(tmp_path):
    zip_path = create_sample_zip_with_various_types(tmp_path)
    result = parse_zip_file(str(zip_path))

    assert result is not None
    assert isinstance(result, list)

    # Check all expected extensions are present
    extensions = {f["extension"] for f in result}
    expected_extensions = {
        ".txt", ".csv", ".docx", ".pdf", 
        ".py", ".java", ".js", ".html", ".css", ".c", ".cpp", ".h"
    }
    assert expected_extensions.issubset(extensions)

    # Check classification
    file_types = {f["file_type"] for f in result}
    assert "text" in file_types
    assert "code" in file_types

    # Check metadata fields
    for entry in result:
        for key in ["file_path", "file_name", "extension", "file_type", "size_bytes", "created", "modified"]:
            assert key in entry


def test_parse_zip_file_invalid_path_returns_none(tmp_path):
    bad_path = tmp_path / "does_not_exist.zip"
    result = parse_zip_file(str(bad_path))
    assert result is None


def test_parse_zip_file_non_zip_file_returns_none(tmp_path):
    fake_file = tmp_path / "not_a_zip.txt"
    fake_file.write_text("hello")

    result = parse_zip_file(str(fake_file))
    assert result is None

def test_parse_zip_file_fake_zip_extension_returns_none(tmp_path):
    fake_zip = tmp_path / "fake.zip"
    fake_zip.write_text("This is not a real ZIP folder")

    result = parse_zip_file(fake_zip)
    assert result is None

def test_collect_file_info_returns_metadata(tmp_path):
    # Create a single file and scan the directory
    f = tmp_path / "example.py"
    f.write_text("print('hi')")

    result = collect_file_info(str(tmp_path))
    assert len(result) == 1

    info = result[0]
    assert info["file_name"] == "example.py"
    assert info["extension"] == ".py"
    assert info["file_type"] == "code"
    assert "size_bytes" in info
    assert "created" in info
    assert "modified" in info

# testing empty zip file
def test_parse_zip_file_empty_zip(tmp_path):
    #Create empty zip file
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w") as f:
        pass

    result = parse_zip_file(empty_zip)
    assert result == []

def test_parse_zip_file_corrupted_zip_returns_none(tmp_path):
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_bytes(b"PK\x03\x04\x00\x00\x00\x00\x00")  # looks like a header but incomplete 

    result = parse_zip_file(str(corrupt_zip))
    assert result is None
    
def test_parse_zip_file_with_unsupported_files(tmp_path):
    zip_path = tmp_path / "unsupported_files.zip"
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "photo.png").write_text("fake image content")
    (content_dir / "virus.exe").write_text("binary data")

    with zipfile.ZipFile(zip_path, "w") as z:
        for file in content_dir.iterdir():
            z.write(file, file.name)

    result = parse_zip_file(str(zip_path))
    assert all(f["extension"] not in {".png", ".exe"} for f in result)

    assert os.path.exists(UNSUPPORTED_LOG_PATH)
    
def test_parse_zip_file_with_duplicate_files(tmp_path):
    zip_path = tmp_path / "duplicates.zip"
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    # Create two identical files with same name in the same folder
    (content_dir / "main.py").write_text("print('a')")
    (content_dir / "main_copy.py").write_text("print('a')")

    # Create ZIP where both are added to the same relative path to simulate duplicate
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(content_dir / "main.py", "code/main.py")
        z.write(content_dir / "main_copy.py", "code/main.py")  # same arcname (duplicate)

    result = parse_zip_file(str(zip_path))

    assert isinstance(result, list)

    file_names = [f["file_name"] for f in result]
    assert file_names.count("main.py") <= 1

    assert os.path.exists(DUPLICATE_LOG_PATH)

    with open(DUPLICATE_LOG_PATH, "r", encoding="utf-8") as f:
        logged_duplicates = json.load(f)
    assert any("code/main.py" in d for d in logged_duplicates)
    
def test_parse_zip_file_detects_duplicates_across_folders(tmp_path):
    # Create temporary files with identical name and content
    zip_path = tmp_path / "duplicate_across_folders.zip"
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    # Two identical files (same name + same content)
    (content_dir / "data1.txt").write_text("hello")
    (content_dir / "data2.txt").write_text("hello")  # same content & size

    # Create ZIP where they exist in different folders but have same name
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(content_dir / "data1.txt", "folderA/report.txt")
        z.write(content_dir / "data2.txt", "folderB/report.txt")

    result = parse_zip_file(str(zip_path))

    assert isinstance(result, list)
    assert os.path.exists(DUPLICATE_LOG_PATH)

    with open(DUPLICATE_LOG_PATH, "r", encoding="utf-8") as f:
        logged_duplicates = json.load(f)

    assert any("folderB/report.txt" in d for d in logged_duplicates)



