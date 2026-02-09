import re

def extract_document_sections(full_text: str):
    """
    Detect headers OR paragraph previews.
    Return list of {header, preview, text}.
    """

    lines = full_text.split("\n")
    sections = []
    buffer = []
    current_header = None

    header_pattern = re.compile(r"^[A-Z][A-Za-z ]{2,}$")  # e.g. "Introduction", "Method"

    for line in lines:
        stripped = line.strip()

        if header_pattern.match(stripped):  # header detected
            # flush previous section
            if buffer:
                section_text = "\n".join(buffer).strip()
                sections.append({
                    "header": current_header,
                    "preview": section_text[:60],
                    "text": section_text
                })
                buffer = []

            current_header = stripped
        else:
            buffer.append(stripped)

    # flush last
    if buffer:
        section_text = "\n".join(buffer).strip()
        sections.append({
            "header": current_header,
            "preview": section_text[:60],
            "text": section_text
        })

    # If NO headers at all → use paragraph previews
    if all(s["header"] is None for s in sections):
        paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
        sections = []
        for p in paragraphs:
            preview = " ".join(p.split()[:5])
            sections.append({
                "header": None,
                "preview": preview + "...",
                "text": p
            })

    return sections