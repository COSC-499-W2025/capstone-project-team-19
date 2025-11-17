import os
import zipfile
from pathlib import Path

from src.utils.parsing import parse_zip_file, analyze_project_layout


def _create_zip_with_markdown(tmp_path: Path) -> Path:
    zip_path = tmp_path / "md_project.zip"
    root = tmp_path / "workspace"
    (root / "Individual" / "solo-notes").mkdir(parents=True, exist_ok=True)
    (root / "Individual" / "solo-notes" / "README.md").write_text("# Solo Notes\n")

    with zipfile.ZipFile(zip_path, "w") as z:
        for file in root.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(tmp_path)
                z.write(file, arcname=str(arcname))
            elif not any(file.iterdir()):
                arcname = file.relative_to(tmp_path)
                z.writestr(str(arcname) + "/", "")
    return zip_path


def test_parse_zip_file_includes_markdown(tmp_path):
    zip_path = _create_zip_with_markdown(tmp_path)
    files = parse_zip_file(str(zip_path))
    extensions = {entry["extension"] for entry in files}
    assert ".md" in extensions
    assert any(entry["file_type"] == "text" for entry in files if entry["extension"] == ".md")


def test_analyze_project_layout_with_buckets():
    files = [
        {"file_path": "workspace/Individual/project_alpha/main.py", "file_name": "main.py"},
        {"file_path": "workspace/Collaborative/project_beta/app.py", "file_name": "app.py"},
        {"file_path": "workspace/COLLABORATIVE/project_notes/summary.md", "file_name": "summary.md"},
    ]

    layout = analyze_project_layout(files)
    assert layout["root_name"] == "workspace"
    assert layout["auto_assignments"] == {
        "project_alpha": "individual",
        "project_beta": "collaborative",
        "project_notes": "collaborative",
    }
    assert layout["pending_projects"] == []


def test_analyze_project_layout_without_buckets():
    files = [
        {"file_path": "workspace/project_one/main.py", "file_name": "main.py"},
        {"file_path": "workspace/project_two/src/index.js", "file_name": "index.js"},
    ]

    layout = analyze_project_layout(files)
    assert layout["root_name"] == "workspace"
    assert layout["auto_assignments"] == {}
    assert layout["pending_projects"] == ["project_one", "project_two"]


def test_analyze_project_layout_single_project_root():
    files = [
        {"file_path": "solo/main.py", "file_name": "main.py"},
        {"file_path": "solo/utils.py", "file_name": "utils.py"},
    ]

    layout = analyze_project_layout(files)
    assert layout["root_name"] == "solo"
    assert layout["auto_assignments"] == {}
    assert layout["pending_projects"] == ["solo"]
