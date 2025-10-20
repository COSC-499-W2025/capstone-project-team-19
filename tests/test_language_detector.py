import pytest
import tempfile
import os
import json
from language_detector import detect_languages


# Test language detection
def test_single_python():
    """Project with a single Python file"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "main.py"), "w").write("print('hi')")
        langs = detect_languages(d)
        assert "Python" in langs

def test_multi_language():
    """Project with multiple recognized code files"""
    with tempfile.TemporaryDirectory() as d:
        files = {
            "app.py": "print('hi')",
            "script.js": "console.log('hi')",
            "index.html": "<html></html>",
            "style.css": "body{}",
            "main.c": "#include <stdio.h>",
            "native.cpp": "#include <iostream>",
        }
        for fname, content in files.items():
            open(os.path.join(d, fname), "w").write(content)
        langs = detect_languages(d)
        for l in ["Python", "JavaScript", "HTML", "CSS", "C", "C++"]:
            assert l in langs

def test_non_code_project():
    """Project with no recognized code files"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "README.md"), "w").write("Hello")
        open(os.path.join(d, "image.png"), "wb").write(b"fake")
        langs = detect_languages(d)
        assert langs == []


