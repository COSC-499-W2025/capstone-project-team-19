def prompt_manual_summary(main_file_name: str) -> str:
    """
    Non-LLM fallback: prompt the user once for a brief summary of the main file.
    """
    print(f"\nMain file: {main_file_name}")
    print("LLM consent not granted. Please enter a 1–2 sentence summary for this file.")
    summary = input("Summary (press Enter to skip): ").strip()
    if not summary:
        return "[No summary provided]"
    return summary
