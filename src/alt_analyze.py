
import os
from typing import Dict, List, Tuple
from datetime import datetime

# NLP and analysis
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
import src.parsing
from src.helpers import extract_text_file

##TODO: Text Extraction (from pdf, txt, docx)✅
##      Linguistic + Readability analysis 
##      Topic modelling
##      Metrics to be produced: Summary, Project Ranking, Activity frequency timeline, Key skills, Success indicators, Work type breakdown, collaboration share




def nltk_data():
    #download nltk data
    requireddata=[
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', "punkt_tab"),
        ('corpora/stopwords', 'stopwords'),
        ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng')

    ]

    for path, package in requireddata:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f'Downloading NLTK:{package}...')
            nltk.download(package, quiet=True)

nltk_data()

#linguistic and readability analysis

def analyze_linguistic_complexity(text: str)->Dict[str, any]:
    if not text or len(text.strip())==0:
        return {
        'word_count': 0,
        'sentence_count': 0,
        'char_count': 0,
        'avg_word_length': 0,
        'avg_sentence_length': 0,
        'lexical_diversity': 0,
        'flesch_reading_ease': 0,
        'flesch_kincaid_grade': 0,
        'smog_index': 0,
        'reading_level': 'N/A'
        }
    
    tokens = [w for w in word_tokenize(text) if w.isalpha()]
    word_count = len(tokens)
    sentence_count=len(sent_tokenize(text))
    char_count=len(text)

    #readability analysis
    flesch_reading_ease=textstat.flesch_reading_ease(text)
    flesch_kincaid_grade=textstat.flesch_kincaid_grade(text)
    smog_index=textstat.smog_index(text)

    #lexical diversity
    words=word_tokenize(text.lower())
    unique_words=set(words)
    lexicaldiversity=len(unique_words)/word_count if word_count>0 else 0

    #average length
    word_average=char_count/word_count
    sentence_average=word_count/sentence_count

    return{
        'word_count': word_count,
        'sentence_count': sentence_count,
        'char_count': char_count,
        'avg_word_length': round(word_average, 2),
        'avg_sentence_length': round(sentence_average, 2),
        'lexical_diversity': round(lexicaldiversity, 3),
        'flesch_reading_ease': round(flesch_reading_ease, 2),
        'flesch_kincaid_grade': round(flesch_kincaid_grade, 2),
        'smog_index': round(smog_index, 2),
        'reading_level': _interpret_reading_level(flesch_kincaid_grade)
    }

def _interpret_reading_level(grade: float) -> str:
    if grade < 6:
        return "Elementary"
    elif grade < 9:
        return "Middle School"
    elif grade < 13:
        return "High School"
    elif grade < 16:
        return "College"
    else:
        return "Graduate"

# topic modelling
def topic_extraction(text: str, n_topics: int=5, n_words: int=10)->List[Dict[str, any]]:
    # n_topics: number of topics to extract
    #n_words: Number of top words per topic
    if not text:
        return[]
    stop_words=set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    pos_tags = nltk.pos_tag(tokens)
    words = [
        word for word, pos in pos_tags
        if (pos.startswith('NN') or pos.startswith('JJ'))
        and word.isalpha()
        and word not in stop_words
        and len(word) >2
    ]

    clean_text=' '.join(words)

    vectorizer=CountVectorizer(max_features=1000, min_df=1, max_df=1.0)
    try:
        doc_term=vectorizer.fit_transform([clean_text])
        lda=LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(doc_term)
        topics=[]
        featurenames=vectorizer.get_feature_names_out()
        for topic_idx, topic in enumerate(lda.components_):
            top_index=topic.argsort()[-n_words:][::-1]
            top_words=[featurenames[i] for i in top_index]
            top_weights=[float(topic[i]) for i in top_index]

            topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weights': top_weights,
                'label':', '.join(top_words[:3]).title()
            })

        return topics
    except Exception as e:
        return[]

def extract_keywords(text: str, n_words: int=20)->List[Tuple[str,float]]:
    stop_words=set(stopwords.words('english'))
    stop_words.update({'al', 'et', 'etc', 'ie', 'eg', 'cf'})
    try:
        tokens = word_tokenize(text.lower())
        pos_tags = nltk.pos_tag(tokens)
        noun_adj_tokens = [
            word for word, pos in pos_tags
            if pos.startswith('NN') or pos.startswith('JJ')
        ]
        filtered_text = ' '.join(noun_adj_tokens)
        vectorizer=TfidfVectorizer(
            max_features=100,
            stop_words=list(stop_words),
            ngram_range=(1,2),
            #token_pattern=r'(?u)\b[a-z]{3,}\b'
        )
        tfidf_mat=vectorizer.fit_transform([filtered_text])
        feature_names=vectorizer.get_feature_names_out()

        scores=tfidf_mat.toarray()[0]
        top_index=scores.argsort()[-n_words:][::-1]
        keywords=[(feature_names[i], float(scores[i])) for i in top_index if scores[i]>0]
        return keywords
    except Exception as e:
        print(f"Error:{e}")
        return []

def calculate_document_metrics(filepath: str)-> Dict[str, any]: 
    text=extract_text_file(filepath)
    if not text:
        return{
            'file_path':filepath,
            'error': 'Failed to extract text',
            'processed': False
        }
    
    linguistic_metrics= analyze_linguistic_complexity(text)
    topics=topic_extraction(text, n_topics=1, n_words=5)
    keywords=extract_keywords(text, n_words=5)

    return{
 
        'processed': True,
        'linguistic_metrics': linguistic_metrics,
        'topics':topics,
        'keywords':keywords[:10],
        'processing_timestamp':datetime.now().isoformat()

    }

def calculate_project_metrics(documents_metrics: List[Dict])->Dict[str,any]:
    if not documents_metrics:
        return{}
    valid_docs=[d for d in documents_metrics if d.get('processed', False)]

    if not valid_docs:
        return {'error':'No documents processed'}

    total_word_count=sum(d['linguistic_metrics']['word_count'] for d in valid_docs)
    total_docs=len(valid_docs)
    reading_level_average=np.mean([d['linguistic_metrics']['flesch_kincaid_grade'] for d in valid_docs])

    all_keywords={}
    for doc in valid_docs:
        for word, score in doc.get('keywords', []):
            all_keywords[word]=all_keywords.get(word, 0)+score

    top_keywords=sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:20]
    return{
        'summary':{
            'total_documents':total_docs,
            'total_words':total_word_count,
            'reading_level_average': round(reading_level_average,2),
            'reading_level_label':_interpret_reading_level(reading_level_average)
        },
        'keywords': [{'word': word, 'score': round(score, 3)} for word, score in top_keywords]
    }

def alternative_analysis(parsed_files, zip_path, project_name, classification_id):
    """
    Main analysis function for alternative (non-LLM) analysis.
    Analyzes the provided files (already grouped by project from project_analysis.py).

    Args:
        parsed_files: List of file info dicts for a single project
        zip_path: Path to the ZIP file
        project_name: Optional name of the project being analyzed
    """
    if not isinstance(parsed_files, list):
        return

    text_files=[f for f in parsed_files if f.get('file_type')=='text']

    if not text_files:
        print("No text files found to analyze.")
        return

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    # Ask user for project summary (optional)
    user_summary = None
    if project_name:
        print(f"\n{'─'*80}")
        print(f"Project: {project_name}")
        summary_input = input("  Brief summary of this project (press Enter to skip): ").strip()
        if summary_input:
            user_summary = summary_input
            print("  ✓ Summary saved")
        else:
            print("  ⊗ Skipped")
        print(f"{'─'*80}\n")

    print(f"\n{'='*80}")
    print(f"ANALYZING {len(text_files)} FILE(S)")
    print(f"{'='*80}\n")

    # Calculate metrics for each document
    all_document_metrics = []
    for file_info in text_files:
        file_path = os.path.join(base_path, file_info['file_path'])
        filename = file_info['file_name']

        print(f"Processing: {filename}")
        doc_metrics = calculate_document_metrics(file_path)

        if doc_metrics.get('processed'):
            doc_metrics['filename'] = filename
            all_document_metrics.append(doc_metrics)
            display_individual_results(filename, doc_metrics)
        else:
            print(f"Failed to process: {doc_metrics.get('error', 'Unknown error')}\n")

    # Display project summary
    if all_document_metrics:
        print(f"\n{'='*80}")
        if project_name:
            print(f"PROJECT SUMMARY - {project_name}")
        else:
            print("PROJECT SUMMARY")
        print(f"{'='*80}\n")

        if user_summary:
            print(f"Your Summary:")
            print(f"  {user_summary}\n")
            print(f"{'─'*80}\n")

        display_project_summary(calculate_project_metrics(all_document_metrics))
    else:
        print("\nNo files were successfully processed.")

def display_individual_results(filename: str, doc_metrics: dict):
    """Display analysis results for an individual file."""
    linguistic = doc_metrics['linguistic_metrics']
    topics = doc_metrics['topics']
    keywords = doc_metrics['keywords']

    print(f"  Linguistic & Readability:")
    print(f"    Word Count: {linguistic['word_count']}, Sentences: {linguistic['sentence_count']}")
    print(f"    Reading Level: {linguistic['reading_level']} (Grade {linguistic['flesch_kincaid_grade']})")
    print(f"    Lexical Diversity: {linguistic['lexical_diversity']}")

    print(f"  Top Keywords: ", end="")
    if keywords:
        keyword_str = ', '.join([word for word, _score in keywords[:5]])
        print(keyword_str)
    else:
        print("None")

    print(f"  Topics: ", end="")
    if topics:
        topic_labels = [topic['label'] for topic in topics[:2]]
        print(', '.join(topic_labels))
    else:
        print("None")
    print()

def display_project_summary(project_metrics: dict):
    """Display aggregated project-wide metrics."""
    if not project_metrics or 'error' in project_metrics:
        print("Unable to generate project summary.")
        return

    summary = project_metrics['summary']
    print(f"Total Documents Analyzed:     {summary['total_documents']}")
    print(f"Total Words:                  {summary['total_words']:,}")
    print(f"Average Reading Level:        {summary['reading_level_label']} (Grade {summary['reading_level_average']})")

    print(f"\nTop Keywords Across All Documents:")
    print("-" * 50)
    keywords = project_metrics.get('keywords', [])
    if keywords:
        for i, kw in enumerate(keywords[:5], 1):
            print(f"{i:2d}. {kw['word']:30s} (score: {kw['score']:.3f})")
    else:
        print("No keywords found")

    print(f"\n{'='*80}\n")

def display_all_projects_summary(all_projects_results: List[Dict]):
    """Display an overall summary comparing all analyzed projects."""
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY - All Projects Combined")
    print(f"{'='*80}\n")

    print(f"Total Projects Analyzed: {len(all_projects_results)}\n")

    # Calculate totals across all projects
    total_files = sum(p['file_count'] for p in all_projects_results)
    total_words_all = sum(p['summary']['summary']['total_words'] for p in all_projects_results)

    print(f"Combined Statistics:")
    print(f"  Total Files Processed:      {total_files}")
    print(f"  Total Words Across Projects: {total_words_all:,}")

    print(f"\nPer-Project Breakdown:")
    print("-" * 80)

    for project_result in all_projects_results:
        project_name = project_result['project_name']
        summary = project_result['summary']['summary']
        file_count = project_result['file_count']

        print(f"\n  Project: {project_name}")
        print(f"    Files:         {file_count}")
        print(f"    Total Words:   {summary['total_words']:,}")
        print(f"    Reading Level: {summary['reading_level_label']} (Grade {summary['reading_level_average']})")

    print(f"\n{'='*80}\n")



