
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

# Text extraction
import docx2txt
import fitz  # PyMuPDF
from pypdf import PdfReader
from docx import Document

# NLP and analysis
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
import parsing

##TODO: Text Extraction (from pdf, txt, docx)✅
##      Linguistic + Readability analysis 
##      Topic modelling
##      Metrics to be produced: Summary, Project Ranking, Activity frequency timeline, Key skills, Success indicators, Work type breakdown, collaboration share




def nltk_data():
    #download nltk data
    requireddata=[
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', "punkt_tab"),
        ('corpora/stopwords', 'stopwords')
    ]

    for path, package in requireddata:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f'Downloading NLTK:{package}...')
            nltk.download(package, quiet=True)

nltk_data()

SUPPORTED_EXTENSIONS={'.txt', '.pdf','.docx'}

## Text Extraction

def extractfile(filepath: str)->Optional[str]: #extract text
    extension=os.path.splitext(filepath)[1].lower()
    if(extension) not in SUPPORTED_EXTENSIONS:
        return None
    
    try:
        if extension=='.txt':
            return extractfromtxt(filepath)
        elif extension == '.pdf':
            return extractfrompdf(filepath)
        elif extension == '.docx':
            return extractfromdocx(filepath)
    except Exception as e:
        return None  
    return None

def extractfromtxt(filepath:str)->str:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extractfrompdf(filepath:str)->str:
    text=[]
    try:
        pdf=fitz.open(filepath)
        for page in pdf:
            text.append(page.get_text())
        pdf.close()
        return '\n'.join(text)
    except Exception as e:
        print(f"Error: {e}")
        return ""

def extractfromdocx (filepath: str)->str:
    try:
        text=docx2txt.process(filepath)
        if text:
            return text
    except Exception as e:
        print(f"Error : {e}")

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
    
    word_count=len(word_tokenize(text))
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
    words=word_tokenize(text.lower())
    words=[w for w in words if w.isalpha() and w not in stop_words and len(w)>2]
    
    clean_text=' '.join(words)

    vectorizer=CountVectorizer(max_features=1000, min_df=1, max_df=1.0)
    try:
        doc_term=vectorizer.fit_transform([clean_text])
        lda=LatentDirichletAllocation(n_components=min(n_topics, 3), random_state=42)
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
    try:
        vectorizer=TfidfVectorizer(
            max_features=100,
            stop_words=list(stop_words),
            ngram_range=(1,2)
        )
        tfidf_mat=vectorizer.fit_transform([text])
        feature_names=vectorizer.get_feature_names_out()

        scores=tfidf_mat.toarray()[0]
        top_index=scores.argsort()[-n_words:][::-1]
        keywords=[(feature_names[i], float(scores[i])) for i in top_index if scores[i]>0]
        return keywords
    except Exception as e:
        print(f"Error:{e}")
        return []

##      Metrics to be produced: Summary, Project Ranking, Activity frequency timeline, Key skills, Success indicators, Work type breakdown, collaboration share

def calculate_document_metrics(filepath: str)-> Dict[str, any]: 
    text=extractfile(filepath)
    if not text:
        return{
            'file_path':filepath,
            'error': 'Failed to extract text',
            'processed': False
        }
    
    linguistic_metrics= analyze_linguistic_complexity(text)
    topics=topic_extraction(text)
    keywords=extract_keywords(text)

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
    
    top_keywords=sorted(all_keywords.items(), key=lambda x: x[1], reversed=True)[:20]
    return{
        'summary':{
            'total_documents':total_docs,
            'total_words':total_word_count,
            'reading_level_average': round(reading_level_average,2),
            'reading_level_label':_interpret_reading_level(reading_level_average)
        },
        'keywords': [{'word': word, 'score': round(score, 3)} for word, score in top_keywords]
    }

