
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

# Text extraction
import docx2txt
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
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


