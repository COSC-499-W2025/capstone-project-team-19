import pandas as pd
import numpy as np
import os
import pytest
from src.analysis.text_individual import csv_analyze as ca


# analyze_single_csv()
def test_basic_numeric_dataset():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
    result = ca.analyze_single_csv(df)

    assert result["row_count"] == 3
    assert result["col_count"] == 3
    assert result["missing_rows"] == 0
    assert result["missing_pct"] == 0.0
    assert result["headers"] == ["A", "B", "C"]
    assert result["dtypes"]["A"] == "int64"


def test_dataset_with_missing_rows():
    df = pd.DataFrame({"A": [1, np.nan, 3], "B": [4, 5, np.nan]})
    result = ca.analyze_single_csv(df)

    assert result["row_count"] == 3
    assert result["missing_rows"] == 2    # rows 1 and 2 contain NaN
    assert result["missing_pct"] == 66.67


def test_mixed_datatypes():
    df = pd.DataFrame({"Text": ["a", "b"], "Num": [1, 2]})
    result = ca.analyze_single_csv(df)

    assert result["col_count"] == 2
    assert result["dtypes"]["Text"] == "object"
    assert result["dtypes"]["Num"] in ["int64", "float64"]


def test_empty_dataset():
    df = pd.DataFrame(columns=["A", "B"])
    result = ca.analyze_single_csv(df)

    assert result["row_count"] == 0
    assert result["missing_rows"] == 0
    assert result["missing_pct"] == 0.0


def test_all_missing_values():
    df = pd.DataFrame({"A": [np.nan, np.nan]})
    result = ca.analyze_single_csv(df)

    assert result["row_count"] == 2
    assert result["missing_rows"] == 2
    assert result["missing_pct"] == 100.0


# load_csv()
def test_load_csv_invalid_path(tmp_path):
    fake = tmp_path / "missing.csv"
    result = ca.load_csv(str(fake))
    assert result is None


# group_csv_files()
def test_group_csv_files():
    csv_files = [
        {"file_name": "data1.csv"},
        {"file_name": "data2.csv"},
        {"file_name": "growth.csv"},
    ]

    groups = ca.group_csv_files(csv_files)

    assert "data" in groups
    assert "growth" in groups
    assert len(groups["data"]) == 2


# analyze_all_csv()
def test_analyze_all_csv(tmp_path, monkeypatch):
    # Create temporary CSV files
    project_dir = tmp_path / "proj"
    project_dir.mkdir()

    # Fake parsed_files
    parsed_files = [
        {"file_name": "data1.csv", "file_path": "data1.csv"},
        {"file_name": "data2.csv", "file_path": "data2.csv"},
    ]

    df1 = pd.DataFrame({"A": [1, 2]})
    df2 = pd.DataFrame({"A": [1, 2, 3]})

    df1.to_csv(project_dir / "data1.csv", index=False)
    df2.to_csv(project_dir / "data2.csv", index=False)

    # Patch ZIP_DATA_DIR to point to tmp_path
    monkeypatch.setattr(
        ca,
        "os",
        ca.os  # need original module
    )
    monkeypatch.setattr(
        ca.os.path,
        "join",
        lambda *args: project_dir / args[-1]
    )

    result = ca.analyze_all_csv(parsed_files, zip_path=str(project_dir))

    assert result["growth_trend_present"] is True
    assert "data" in result["growth_trends"]
    assert result["files"][0]["col_count"] == 1
