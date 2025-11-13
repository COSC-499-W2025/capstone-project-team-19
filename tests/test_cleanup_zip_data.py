from pathlib import Path

from src.common.helpers import cleanup_extracted_zip


def test_cleanup_extracted_zip_removes_workspace(tmp_path):
    project_root = Path(__file__).resolve().parents[1]  
    src_root = project_root / "src"
    zip_data_dir = src_root / "analysis" / "zip_data"

    # create a fake extracted workspace
    (zip_data_dir / "sample_project").mkdir(parents=True, exist_ok=True)

    fake_zip = tmp_path / "sample_project.zip"
    fake_zip.write_text("placeholder")

    cleanup_extracted_zip(str(fake_zip))
    assert not zip_data_dir.exists()

    # Ensure subsequent calls remain safe when directory is already gone
    cleanup_extracted_zip(str(fake_zip))
    assert not zip_data_dir.exists()
