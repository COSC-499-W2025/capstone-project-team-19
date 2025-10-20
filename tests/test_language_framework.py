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

# Framework Tests
def test_python_frameworks():
    """Detect Python frameworks"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "requirements.txt"), "w").write("Django\npytest\npandas")
        fws = detect_frameworks(d)
        for fw in ["Django", "pytest", "Pandas"]:
            assert fw in fws

def test_js_frameworks():
    """Detect JS frameworks"""
    with tempfile.TemporaryDirectory() as d:
        pkg = {"dependencies": {"react": "^18.0.0", "express": "^4.0.0"}}
        json.dump(pkg, open(os.path.join(d, "package.json"), "w"))
        fws = detect_frameworks(d)
        for fw in ["React", "Express.js"]:
            assert fw in fws

def test_java_framework():
    """Detect Java frameworks"""
    with tempfile.TemporaryDirectory() as d:
        pom = "<project><dependencies><dependency><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>"
        open(os.path.join(d, "pom.xml"), "w").write(pom)
        fws = detect_frameworks(d)
        assert "Spring Boot" in fws

def test_multi_framework_project():
    """Detect multiple frameworks in one project"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "requirements.txt"), "w").write("Flask")
        pkg = {"dependencies": {"react": "^18"}}
        json.dump(pkg, open(os.path.join(d, "package.json"), "w"))
        fws = detect_frameworks(d)
        for fw in ["Flask", "React"]:
            assert fw in fws

def test_no_frameworks_detected():
    """Simple Python project should return no frameworks"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "main.py"), "w").write("print('hello')")
        fws = detect_frameworks(d)
        assert fws == []

def test_non_code_project_frameworks():
    """Non-code project should return no frameworks"""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "README.md"), "w").write("Just a readme")
        fws = detect_frameworks(d)
        assert fws == []

