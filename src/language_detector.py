import os
import json

# Language Detection
EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header"
}

def detect_languages(project_path):
    """Detect languages by file extensions."""
    languages = set()
    for root, _, files in os.walk(project_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in EXTENSION_TO_LANGUAGE:
                languages.add(EXTENSION_TO_LANGUAGE[ext])
    return list(languages)

# Testing
if __name__ == "__main__":
    # add your project path here for manual testing
    project_folder = "C:/Users/ivona/Projects/Hello, Stars!/Hackathon2025"
    detected = detect_languages(project_folder)
    print("Languages detected:", detected)