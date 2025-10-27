import os

FRAMEWORK_KEYWORDS = {
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Pyramid": ["pyramid"],
    "Spring": ["spring-boot", "springframework"],
    "Hibernate": ["hibernate"],
    "React": ["react", "react-dom", "react-scripts", "next", "gatsby", "remix"],
    "Angular": ["@angular/core"],
    "Vue": ["vue", "vite", "nuxt"],
    "Next.js": ["next"],
    "Express": ["express"],
    "NestJS": ["@nestjs/core"],
    "Tailwind CSS": ["tailwindcss", "tailwind.config.js", "tailwind.config.cjs"],
    "Bootstrap": ["bootstrap"],
}

def detect_frameworks(conn, project_name, user_id,zip_path):
    """
    Detect frameworks used in a project by scanning config files.
    Returns a set of framework names.
    """
    #path for accessing files
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    cur = conn.cursor()
    frameworks = set()

    # Fetch all config files for this project & user
    cur.execute("""
        SELECT file_path
        FROM config_files
        WHERE project_name = ? AND user_id = ?
    """, (project_name, user_id))

    files = cur.fetchall()
    if not files:
        return frameworks  # empty set

    for (file_path,) in files:
        full_path = os.path.join(base_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_lower = line.lower()
                    for fw, keywords in FRAMEWORK_KEYWORDS.items():
                        if any(kw in line_lower for kw in keywords):
                            frameworks.add(fw)
        except Exception as e:
            print(f"Could not read {file_path}: {e}")

    return frameworks
