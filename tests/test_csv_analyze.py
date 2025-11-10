import pandas as pd
import numpy as np
import os
import io
import builtins
import pytest
from src import csv_analyze as ca

# analyze individual csvs
def test_basic_numeric_dataset():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
    result = ca.analyze_single_csv(df)
    assert result["row_count"] == 3
    assert result["missing_rows"] == 0
    assert "A" in result["numeric_stats"]
    assert result["numeric_stats"]["B"]["mean"] == 5.0


def test_dataset_with_missing_rows():
    df = pd.DataFrame({"A": [1, np.nan, 3], "B": [4, 5, np.nan], "C": ["x", "y", "z"]})
    result = ca.analyze_single_csv(df)
    assert result["missing_rows"] == 2
    assert pytest.approx(result["missing_pct"], rel=0.1) == 66.67


def test_mixed_datatypes():
    df = pd.DataFrame({"Text": ["a", "b", "c"], "Num": [1, 2, 3]})
    result = ca.analyze_single_csv(df)
    assert "Num" in result["numeric_stats"]
    assert "Text" not in result["numeric_stats"]


def test_empty_dataset():
    df = pd.DataFrame(columns=["A", "B"])
    result = ca.analyze_single_csv(df)
    assert result["row_count"] == 0
    assert result["missing_rows"] == 0


def test_all_missing_values():
    df = pd.DataFrame({"A": [np.nan, np.nan], "B": [np.nan, np.nan]})
    result = ca.analyze_single_csv(df)
    assert result["missing_rows"] == 2
    assert result["missing_pct"] == 100.0


# check if csv is loaded correctly
def test_load_csv_invalid_path(tmp_path):
    fake_path = tmp_path / "missing.csv"
    result = ca.load_csv(str(fake_path))
    assert result is None


# check if csv grouping works (for growth trend)
def test_group_csv_files():
    csv_files = [
        {"file_name": "data1.csv"},
        {"file_name": "data2.csv"},
        {"file_name": "growth.csv"}
    ]
    groups = ca.group_csv_files(csv_files)
    assert "data" in groups
    assert "growth" in groups
    assert len(groups["data"]) == 2


# check if growth trend calculation is accurate
def test_print_growth_trend(capsys):
    trend = [("file1.csv", 100), ("file2.csv", 120)]
    ca.print_growth_trend(trend)
    out = capsys.readouterr().out
    assert "Total Growth: +20.0%" in out


# check if dataset summary generation works with LLM consent
def test_generate_dataset_summary_rejected(monkeypatch):
    df = pd.DataFrame({"A": [1, 2, 3]})
    monkeypatch.setattr(builtins, "input", lambda _: "manual summary here")
    result = ca.generate_dataset_summary(df, "test.csv", llm_consent="rejected")
    assert "manual summary" in result


def test_generate_dataset_summary_api_error(monkeypatch):
    df = pd.DataFrame({"A": [1, 2, 3]})
    def fake_create(*args, **kwargs): raise Exception("API failure")
    monkeypatch.setattr(ca.client.chat.completions, "create", fake_create)
    result = ca.generate_dataset_summary(df, "test.csv", llm_consent="accepted")
    assert "[Summary unavailable" in result
