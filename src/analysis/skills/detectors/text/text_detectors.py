"""
FULL IMPLEMENTATION OF ALL 10 TEXT DETECTORS (SCORING-BASED)
Each detector returns:
    {
        "score": float in [0,1],
        "evidence": list of dicts
    }
"""

import re
from collections import Counter
from src.analysis.text_individual.alt_analyze import analyze_linguistic_complexity
import re
from nltk.corpus import stopwords


def detect_sentence_clarity(file_text: str, file_name: str):
    """
    Criteria (max 4 points):
      1. >= 50% sentences <= 25 words
      2. Avg sentence length <= 20 words
      3. No sentence > 50 words
      4. Variance of sentence length reasonable (< 200)
    """

    sentences = re.split(r'[.!?]+\s+', file_text.strip())
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return {"score": 0, "evidence": []}

    lengths = [len(s.split()) for s in sentences]
    evidence = [{"sentence": s[:60], "length": len(s.split())} for s in sentences]

    score = 0
    total = 4

    if sum(1 for l in lengths if l <= 25) / len(lengths) >= 0.5:
        score += 1
    if (sum(lengths) / len(lengths)) <= 20:
        score += 1
    if max(lengths) <= 50:
        score += 1
    if (max(lengths) - min(lengths)) < 200:
        score += 1

    return {"score": score / total, "evidence": evidence}


def detect_paragraph_structure(file_text: str, file_name: str):
    """
    Criteria (max 4 points):
      1. >= 3 paragraphs
      2. >= 2 paragraphs contain >= 2 sentences
      3. Paragraphs not excessively long (< 250 words)
      4. Paragraph-level transitions detected (keywords)
    """

    paragraphs = [p.strip() for p in file_text.split("\n") if p.strip()]
    if not paragraphs:
        return {"score": 0, "evidence": []}

    evidence = []
    score = 0
    total = 4

    # 1) paragraph count
    if len(paragraphs) >= 3:
        score += 1

    # 2) number of strong paragraphs
    strong = 0
    for p in paragraphs:
        sent_count = len(re.split(r'[.!?]+\s+', p))
        evidence.append({"paragraph_preview": p[:80], "sentence_count": sent_count})
        if sent_count >= 2:
            strong += 1
    if strong >= 2:
        score += 1

    # 3) paragraph length check
    if all(len(p.split()) < 250 for p in paragraphs):
        score += 1

    # 4) transitions
    transitions = ["however", "in addition", "moreover", "furthermore", "overall"]
    if any(t in file_text.lower() for t in transitions):
        score += 1

    return {"score": score / total, "evidence": evidence}


def detect_vocabulary_diversity(file_text: str, file_name: str):
    """
    Criteria (max 4 points):
      1. lexical_diversity >= 0.35
      2. lexical_diversity >= 0.45
      3. FK grade >= 10
      4. FK grade >= 13
    """

    metrics = analyze_linguistic_complexity(file_text)
    lex = metrics.get("lexical_diversity", 0)
    grade = metrics.get("flesch_kincaid_grade", 0)

    score = 0
    total = 4

    if lex >= 0.35: score += 1
    if lex >= 0.45: score += 1
    if grade >= 10: score += 1
    if grade >= 13: score += 1

    return {
        "score": score / total,
        "evidence": [{
            "lexical_diversity": float(lex),
            "FK_grade": float(grade),
            "reading_level": metrics.get("reading_level")
        }]
    }



def detect_argument_structure(file_text: str, file_name: str):
    """
    Criteria (max 4 points):
      1. 1+ claim markers
      2. 1+ evidence markers
      3. 1+ reasoning terms
      4. 1+ conclusion markers
    """

    text_lower = file_text.lower()

    claim_words      = ["i argue", "this suggests", "i claim", "the point is"]
    evidence_words   = ["according to", "data", "research", "study"]
    reasoning_words  = ["because", "therefore", "thus", "hence"]
    conclusion_words = ["in conclusion", "overall", "to conclude"]

    score = 0
    total = 4
    ev = {}

    for label, words in [
        ("claims",      claim_words),
        ("evidence",    evidence_words),
        ("reasoning",   reasoning_words),
        ("conclusions", conclusion_words)
    ]:
        found = [w for w in words if w in text_lower]
        ev[label] = found
        if found:
            score += 1

    return {"score": score / total, "evidence": [ev]}


def detect_depth_of_content(file_text: str, file_name: str):
    """
    Depth detector = conceptual richness + analytical reasoning.
    
    Scoring (4 points):
      1. Abstract/conceptual vocabulary (>=5)
      2. Causal/analytical connectors (>=3)
      3. Idea density (>=0.20)
      4. Interpretation phrases (>=2)
    """

    text_lower = file_text.lower()

    # 1. Abstract / conceptual vocabulary
    abstract_keywords = [
        "concept", "framework", "theory", "model", "analysis",
        "interpretation", "implication", "assumption",
        "perspective", "principle", "underlying"
    ]
    abstract_count = sum(text_lower.count(k) for k in abstract_keywords)

    # 2. Causal / analytical connectors
    connectors = [
        "therefore", "thus", "hence", "consequently", 
        "as a result", "this implies", "this suggests", 
        "this indicates", "results in", "leads to"
    ]
    connector_hits = [c for c in connectors if c in text_lower]

    # 3. Idea density
    stop = set(stopwords.words('english'))

    words = re.findall(r"[A-Za-z]+", text_lower)
    meaningful = [w for w in words if w not in stop]

    unique_meaningful = set(meaningful)
    idea_density = (len(unique_meaningful) / len(words)) if words else 0

    # 4. Interpretation phrases
    interpretation_patterns = [
        "this shows", "this means", "this demonstrates",
        "we can infer", "the implication is"
    ]
    interpretation_hits = [p for p in interpretation_patterns if p in text_lower]

    # ----- Scoring -----
    score = 0
    total = 4

    if abstract_count >= 5:
        score += 1
    if len(connector_hits) >= 3:
        score += 1
    if idea_density >= 0.20:
        score += 1
    if len(interpretation_hits) >= 2:
        score += 1

    evidence = [{
        "abstract_keyword_count": abstract_count,
        "connector_hits": connector_hits,
        "idea_density": round(idea_density, 3),
        "interpretation_hits": interpretation_hits
    }]

    return {"score": score / total, "evidence": evidence}



def detect_iterative_process(file_text: str, file_name: str, supporting_files=None):
    """
    Criteria (max 4 points):
      1. >= 1 draft file
      2. >= 2 drafts
      3. outline file present
      4. version markers in filenames (v2, rev, etc.)
    """

    if not supporting_files:
        return {"score": 0, "evidence": []}

    score = 0
    total = 4
    evidence = [{"file": f["filename"]} for f in supporting_files]

    draft_like = [f for f in supporting_files if any(x in f["filename"].lower() for x in ["draft", "rev", "edit"])]
    version_like = [f for f in supporting_files if any(x in f["filename"].lower() for x in ["v2", "v3"])]
    outline_like = [f for f in supporting_files if "outline" in f["filename"].lower()]

    if len(draft_like) >= 1: score += 1
    if len(draft_like) >= 2: score += 1
    if outline_like: score += 1
    if version_like: score += 1

    return {"score": score / total, "evidence": evidence}


def detect_planning_behavior(file_text: str, file_name: str, supporting_files=None):
    """
    Criteria (max 4 points):
      1. Outline file present
      2. Section markers detected
      3. Bullet lists present
      4. Numbered lists present
    """

    text_lower = file_text.lower()
    score = 0
    total = 4
    evidence = []

    # 1 outline present?
    if supporting_files:
        outlines = [f for f in supporting_files if "outline" in f["filename"].lower()]
        if outlines:
            score += 1
            evidence.extend([{"outline_file": f["filename"]} for f in outlines])

    # 2 section markers
    if any(x in text_lower for x in ["introduction", "method", "conclusion", "overview"]):
        score += 1
        evidence.append({"section_markers": True})

    # 3 bullet lists
    if re.search(r"[-*]\s+\w+", file_text):
        score += 1
        evidence.append({"bullet_list": True})

    # 4 numbered lists
    if re.search(r"\d+\.\s+\w+", file_text):
        score += 1
        evidence.append({"numbered_list": True})

    return {"score": score / total, "evidence": evidence}



def detect_evidence_of_research(file_text: str, file_name: str):
    """
    APA criteria (2 points):
        +1 APA present (Smith, 2020)
        +1 APA count >= 3

    MLA criteria (2 points):
        +1 MLA present (Smith 22)
        +1 MLA count >= 3

    Other research signals (4 points):
        +1 numeric citations [1]
        +1 "according to"
        +1 author-verb pattern ("Smith argues")
        +1 research words ("study", "journal", ...)
    """

    text = file_text
    lower = text.lower()

    score = 0
    total = 8
    evidence = []

    # APA
    apa = re.findall(r"\([A-Za-z]+, \d{4}\)", text)
    if apa:
        score += 1
        evidence.append({"APA_citations": apa})
    if len(apa) >= 3:
        score += 1

    # MLA
    mla = re.findall(r"[A-Z][a-zA-Z]+ \d{1,3}", text)
    if mla:
        score += 1
        evidence.append({"MLA_citations": mla})
    if len(mla) >= 3:
        score += 1

    # numeric citations
    numeric = re.findall(r"\[\d+\]", text)
    if numeric:
        score += 1
        evidence.append({"numeric_citations": numeric})

    # signal phrase
    if "according to" in lower:
        score += 1
        evidence.append({"phrase": "according to"})

    # author verb pattern
    if re.search(r"[A-Z][a-z]+ (argues|notes|claims|states)", text):
        score += 1
        evidence.append({"author_verb_pattern": True})

    # research words
    research_terms = ["study", "journal", "paper", "research", "dataset"]
    if any(r in lower for r in research_terms):
        score += 1
        evidence.append({"research_terms": True})

    return {"score": score / total, "evidence": evidence}


def detect_data_collection(file_text, file_name, supporting_files=None, csv_metadata=None):
    """
    Data collection skill based ONLY on CSV quality/structure, not count of files.

    Criteria (9 total, each worth 1 point):

      1. There is at least one CSV file
      2. At least one CSV has > 1 column
      3. At least one CSV has > 3 columns
      4. At least one CSV has > 1 row
      5. At least one CSV has > 5 rows
      6. At least one CSV has missing_pct < 50%
      7. At least one CSV has missing_pct < 15%
      8. At least one CSV has missing_pct == 0%
      9. growth_trend_present == True in csv_metadata
    """

    if not csv_metadata or not csv_metadata.get("files"):
        # no CSVs → score 0
        return {"score": 0, "evidence": []}

    files = csv_metadata["files"]
    score = 0
    total = 9
    evidence = []

    # We'll keep per-file stats as evidence
    for f in files:
        evidence.append({
            "file_name": f["file_name"],
            "rows": int(f["row_count"]),
            "cols": int(f["col_count"]),
            "missing_pct": float(f["missing_pct"]),
            "headers": list(f["headers"]),
        })

    # helper lambdas
    any_cols_gt_1   = any(f["col_count"] > 1 for f in files)
    any_cols_gt_3   = any(f["col_count"] > 3 for f in files)
    any_rows_gt_1   = any(f["row_count"] > 1 for f in files)
    any_rows_gt_5   = any(f["row_count"] > 5 for f in files)
    any_miss_lt_50  = any(float(f["missing_pct"]) < 50.0 for f in files)
    any_miss_lt_15  = any(float(f["missing_pct"]) < 15.0 for f in files)
    any_miss_eq_0   = any(float(f["missing_pct"]) == 0.0 for f in files)
    has_growth_trend = bool(csv_metadata.get("growth_trend_present"))

    # 1) at least one CSV
    if len(files) >= 1:
        score += 1

    # 2–3) column thresholds
    if any_cols_gt_1:
        score += 1
    if any_cols_gt_3:
        score += 1

    # 4–5) row thresholds
    if any_rows_gt_1:
        score += 1
    if any_rows_gt_5:
        score += 1

    # 6–8) missingness thresholds
    if any_miss_lt_50:
        score += 1
    if any_miss_lt_15:
        score += 1
    if any_miss_eq_0:
        score += 1

    # 9) growth trend
    if has_growth_trend:
        score += 1
        evidence.append({"growth_trend_present": True})

    return {"score": score / total, "evidence": evidence}


def detect_data_analysis(file_text: str, file_name: str, supporting_files=None):
    """
    Criteria (max 4 points):
      1. mentions of results/graph/table ---> 1 point
      2. mentions of statistical terms (correlation/regression) ---> 1 point
      3. mentions of quantitative comparisons (increase/decrease) ---> 1 point
      4. mentions of interpretation ("this shows", "indicates") ---> 1 point
    """

    lower = file_text.lower()
    score = 0
    total = 4
    evidence = []

    if any(k in lower for k in ["result", "graph", "table", "figure"]):
        score += 1
        evidence.append({"visual_reference": True})

    if any(k in lower for k in ["correlation", "regression"]):
        score += 1
        evidence.append({"stat_terms": True})

    if any(k in lower for k in ["increase", "decrease", "trend"]):
        score += 1
        evidence.append({"trend_reference": True})

    if any(k in lower for k in ["shows", "indicates", "suggests"]):
        score += 1
        evidence.append({"interpretation": True})

    return {"score": score / total, "evidence": evidence}




