from parsing import parse_zip_file
from db import connect, init_schema, get_or_create_user, _normalize_username, get_user_by_username, get_latest_consent, get_latest_external_consent
from consent import CONSENT_TEXT, get_user_consent, record_consent
from external_consent import get_external_consent, record_external_consent
from alt_analyze import extractfile, extract_keywords, topic_extraction, analyze_linguistic_complexity
import os

def main():
    print("Welcome aboard! Let’s turn your work into cool insights.")

    # Should be called in main() not __main__ beacsue __main__ does not run during tests
    prompt_and_store()

def prompt_and_store():
    """Main flow: identify user, check prior consents, reuse or re-prompt."""
    conn = connect()
    init_schema(conn)

    username = input("Enter your username: ").strip()
    user_id = get_or_create_user(conn, username)

    prev_consent = get_latest_consent(conn, user_id)
    prev_ext = get_latest_external_consent(conn, user_id)

    reused = False  # track reuse
    current_ext_consent=None 

    # Edge case 1: user exists but no consents yet
    if not prev_consent and not prev_ext:
        print(f"\nWelcome back, {username}!")
        print("Looks like you’ve been here before, but we don’t have your consent record yet.")
        print("Let’s complete your setup.\n")
        print(CONSENT_TEXT)
        status = get_user_consent()
        record_consent(conn, status, user_id=user_id)
        ext_status = get_external_consent()
        record_external_consent(conn, ext_status, user_id=user_id)
        current_ext_consent=ext_status

    # Edge case 2: partial configuration (only one consent found)
    elif (prev_consent and not prev_ext) or (not prev_consent and prev_ext):
        print(f"\nWelcome back, {username}!")
        print("We found a partial configuration:")
        print(f"  • User consent = {prev_consent or 'none'}")
        print(f"  • External service consent = {prev_ext or 'none'}")
        print("Let’s complete your setup.\n")

        # Only ask for the missing one
        if not prev_consent:
            print(CONSENT_TEXT)
            status = get_user_consent()
            record_consent(conn, status, user_id=user_id)
        # Although this is not necessary because you have to answer user consent before going to external consent
        if not prev_ext:
            ext_status = get_external_consent()
            record_external_consent(conn, ext_status, user_id=user_id)
            current_ext_consent=ext_status
        else:
            current_ext_consent=prev_ext

    # --- Returning user with full configuration ---
    elif prev_consent and prev_ext:
        print(f"\nWelcome back, {username}!")
        print(f"Your previous configuration: user consent = {prev_consent}, external service consent = {prev_ext}.")
        reuse = input("Would you like to continue with this configuration? (y/n): ").strip().lower()

        if reuse == "y":
            reused = True
            record_consent(conn, prev_consent, user_id=user_id)
            record_external_consent(conn, prev_ext, user_id=user_id)
            current_ext_consent=prev_ext
        else:
            print("\nAlright, let’s review your consents again.\n")
            print(CONSENT_TEXT)
            status = get_user_consent()
            record_consent(conn, status, user_id=user_id)
            ext_status = get_external_consent()
            record_external_consent(conn, ext_status, user_id=user_id)
            current_ext_consent = ext_status

    # --- Brand new user ---
    else:
        print(f"\nNice to meet you, {username}!\n")
        print(CONSENT_TEXT)
        status = get_user_consent()
        record_consent(conn, status, user_id=user_id)
        ext_status = get_external_consent()
        record_external_consent(conn, ext_status, user_id=user_id)
        current_ext_consent=ext_status

    # Only show message if not reusing previous config
    if not reused:
        print("\nConsent recorded. Proceeding to file selection…\n")
    else:
        print("\nContinuing with your saved configuration…\n")

    # Continue to file selection
    zip_path = get_zip_path_from_user()
    print(f"Recieved path: {zip_path}")
    result = parse_zip_file(zip_path)
    if not result:
        print("No valid files were processed. Check logs for unsupported or corrupted files.")
        return

    analyze_files(conn, user_id, current_ext_consent, result, zip_path)

def analyze_files(conn, user_id, external_consent, parsed_files, zip_path):
    if external_consent=='accepted':
    #for now will only use alternative method
        alternative_analysis(conn, user_id, parsed_files, zip_path)
    else:
        alternative_analysis(conn, user_id, parsed_files, zip_path)

def alternative_analysis(conn, user_id, parsed_files, zip_path):
    text_files=[f for f in parsed_files if f.get('file_type')=='text']
    metrics=[]

    if not text_files:
        return

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    for file_info in text_files:
        file_path = os.path.join(base_path, file_info['file_path'])
        filename = file_info['file_name']
    
    print(f"Analyzing: {filename}")
    text=extractfile(file_path)

    linguistic_analysis= analyze_linguistic_complexity(text)
    topics=topic_extraction(text, n_topics=3, n_words=5)
    keywords=extract_keywords(text, n_words=5)

    metrics.append({
        'filename': filename,
        'file_path': file_info['file_path'],
        'linguistic': linguistic_analysis,
        'topics': topics,
        'keywords': keywords
    })
    display_analysis_results(filename, linguistic_analysis, topics, keywords)

def display_analysis_results(filename:str, linguistic:dict, topics:list, keywords:list):
    print("Linguistic and Readability:\n")
    print(f"Word Count:              {linguistic['word_count']}")
    print(f"Sentence Count:          {linguistic['sentence_count']}")
    print(f"Character Count:         {linguistic['char_count']}")
    print(f"Avg Word Length:         {linguistic['avg_word_length']}")
    print(f"Avg Sentence Length:     {linguistic['avg_sentence_length']}")
    print(f"Lexical Diversity:       {linguistic['lexical_diversity']}")
    print(f"\nReadability Scores:")
    print(f"  Flesch Reading Ease:   {linguistic['flesch_reading_ease']}")
    print(f"  Flesch-Kincaid Grade:  {linguistic['flesch_kincaid_grade']}")
    print(f"  SMOG Index:            {linguistic['smog_index']}")
    print(f"  Reading Level:         {linguistic['reading_level']}")

    print(f'\n Top Keywords:\n')
    if keywords:
        for i, (word, score) in enumerate(keywords[:15], 1):
            print(f"{i:2d}. {word:30s} (score: {score:.4f})")
    else:
        print("No keywords extracted")
    print(f"\nTopics:")
    print("-" * 80)
    if topics:
        for topic in topics:
            print(f"\nTopic {topic['topic_id'] + 1}: {topic['label']}")
            print(f"  Top words: {', '.join(topic['words'][:10])}")
    else:
        print("No topics extracted")
  

def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path

if __name__ == "__main__":
    main()
