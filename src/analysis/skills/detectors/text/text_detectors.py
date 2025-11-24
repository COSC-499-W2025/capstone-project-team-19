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
    Checks for 5 types of writing issues:
      1. Fragments / run-on sentences
      2. Subject–verb agreement errors
      3. Misplaced or dangling modifiers
      4. Wordiness / filler words
      5. Pronoun & homophone clarity issues

    Score = (# criteria passed) / 5

    Evidence = all sentences that violated each rule.
    """

    # Safer sentence splitting (keeps abbreviations intact)
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[\.!?])\s+', file_text.strip())
        if s.strip()
    ]

    if not sentences:
        return {"score": 0, "evidence": {}}

    total_criteria = 5
    score = 0

    # Evidence buckets
    evidence = {
        "fragments_runons": [],
        "subj_verb_agreement": [],
        "misplaced_modifiers": [],
        "wordiness": [],
        "pronoun_homophone": []
    }

    # --- Helper heuristic functions ---

    def is_runon_or_fragment(s: str) -> bool:
        words = s.split()

        # Fragment: too short or missing a verb
        if len(words) < 4 or not re.search(r'\b(is|are|was|were|has|had|does|do|did)\b', s, re.I):
            return True

        # Run-on: extremely long but no commas/semicolons
        if len(words) > 40 and (',' not in s and ';' not in s):
            return True

        return False

    def has_subj_verb_error(s: str) -> bool:
        # Plural nouns incorrectly matched with singular verbs
        if re.search(r'\b(people|students|data|results)\s+is\b', s, re.I):
            return True

        # Singular markers incorrectly matched with plural verbs
        if re.search(r'\b(each|every)\s+\w+\s+are\b', s, re.I):
            return True

        return False

    def is_misplaced_modifier(s: str) -> bool:
        # Dangling participles ("Having done X, Y happened")
        return bool(re.match(r'^(Having|Being|While)\s+\w+', s))

    def is_wordy(s: str) -> bool:
        words = s.split()
        filler = re.search(r'\b(very|really|in addition|furthermore)\b', s, re.I)
        return len(words) > 22 or bool(filler)

    def has_pronoun_homophone_issue(s: str) -> bool:
        # Vague pronoun chains ("this... this... it...")
        if re.search(r'\b(it|this|that)\b.*\b(it|this|that)\b', s, re.I):
            return True

        # Common homophone mixups
        if re.search(r'\b(their|there|they\'re)\b', s, re.I):
            return True
        if re.search(r'\b(its|it\'s)\b', s, re.I):
            return True

        return False

    # --- Evaluate all sentences ---
    for s in sentences:
        if is_runon_or_fragment(s):
            evidence["fragments_runons"].append(s)
        if has_subj_verb_error(s):
            evidence["subj_verb_agreement"].append(s)
        if is_misplaced_modifier(s):
            evidence["misplaced_modifiers"].append(s)
        if is_wordy(s):
            evidence["wordiness"].append(s)
        if has_pronoun_homophone_issue(s):
            evidence["pronoun_homophone"].append(s)

    # --- Scoring rules ---
    # Less than 5% of sentences should have these errors (or max 1)
    threshold_5 = max(1, int(len(sentences) * 0.05))
    threshold_10 = max(1, int(len(sentences) * 0.10))

    # Criterion 1: fragments/run-ons
    if len(evidence["fragments_runons"]) <= threshold_5:
        score += 1

    # Criterion 2: subject-verb agreement
    if len(evidence["subj_verb_agreement"]) == 0:
        score += 1

    # Criterion 3: misplaced modifiers
    if len(evidence["misplaced_modifiers"]) <= threshold_5:
        score += 1

    # Criterion 4: wordiness
    if len(evidence["wordiness"]) <= threshold_10:
        score += 1

    # Criterion 5: pronoun/homophone misuse
    if len(evidence["pronoun_homophone"]) <= threshold_5:
        score += 1

    return {
        "score": score / total_criteria,
        "evidence": evidence
    }



def detect_paragraph_structure(file_text: str, file_name: str):
    """
    Criteria (max 4 points):
      1. >= 3 paragraphs
      2. >= 2 paragraphs contain >= 2 sentences
      3. Paragraphs not excessively long (< 250 words)
      4. Paragraph-level transitions detected (keywords)
    """

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", file_text) if p.strip()]
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

    claim_words      = ["i argue", "this paper argues", "i propose", "the thesis is", "the point is"]
    evidence_words   = ["according to", "the study shows", "data from", "research indicates", "evidence suggests"]
    reasoning_words  = ["because", "therefore", "as a result", "thus", "hence", "this implies"]
    conclusion_words = ["in conclusion", "to conclude", "overall", "in sum", "in closing"]

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
      1. Abstract/conceptual vocabulary (>=5 unique whole-word matches)
      2. Causal/analytical connectors (>=3)
      3. Idea density >= 0.20 AND text >= 80 words
      4. Interpretation phrases (>=2)
    """

    text_lower = file_text.lower()

    # Tokenize words
    words = re.findall(r"[A-Za-z]+", text_lower)
    word_count = len(words)

    # If text is too short, idea-density is meaningless → auto score = 0
    if word_count < 80:
        return {
            "score": 0,
            "evidence": [{
                "reason": "text too short (<80 words for reliable depth analysis)",
                "word_count": word_count
            }]
        }

    # 1. Abstract/conceptual vocabulary (whole-word matching)
    abstract_keywords = [
        "concept", "framework", "theory", "model", "analysis",
        "interpretation", "implication", "assumption",
        "perspective", "principle", "underlying"
    ]

    abstract_count = 0
    for kw in abstract_keywords:
        # whole-word boundaries only
        if re.search(rf"\b{kw}\b", text_lower):
            abstract_count += 1

    # 2. Causal / analytical connectors (must appear as substrings but normalized)
    connectors = [
        "therefore", "thus", "hence", "consequently",
        "as a result", "this implies", "this suggests",
        "this indicates", "results in", "leads to"
    ]
    connector_hits = [c for c in connectors if c in text_lower]

    # 3. Idea density (meaningful words per total words)
    stop = set(stopwords.words('english'))

    meaningful = [w for w in words if w not in stop]
    unique_meaningful = set(meaningful)

    idea_density = len(unique_meaningful) / word_count if word_count else 0

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
        "interpretation_hits": interpretation_hits,
        "word_count": word_count
    }]

    return {"score": score / total, "evidence": evidence}



def detect_iterative_process(file_text: str, file_name: str, supporting_files=None):
    """
    Iterative process detector.

    Scoring (4 points):
      1. >= 1 draft file (whole-word match)
      2. >= 2 drafts
      3. Outline file present
      4. Version markers detected (v# or "version #")
    """

    if not supporting_files:
        return {"score": 0, "evidence": []}

    score = 0
    total = 4

    evidence = []
    draft_files = []
    version_files = []
    outline_files = []

    for f in supporting_files:
        fname = f["filename"]
        lower = fname.lower()

        # record all filenames regardless
        evidence.append({"file": fname})

        # --- 1) DRAFT DETECTION (whole word only) ---
        # Ensures "final_draft_v3" → counts as draft (once), not "pendraft" etc.
        if re.search(r"\bdraft\b|\brev(?:ision)?\b", lower):
            draft_files.append(fname)

        # --- 2) OUTLINE DETECTION ---
        if re.search(r"\boutline\b", lower):
            outline_files.append(fname)

        # --- 3) VERSION DETECTION (v2, v10, version 3, etc.) ---
        # Captures: v2, V3, v10, version2, version 2, revision 3
        if re.search(r"\bv\s*\d+\b|\bversion\s*\d+\b", lower):
            version_files.append(fname)

    # ---------- Scoring ----------
    if len(draft_files) >= 1:
        score += 1
    if len(draft_files) >= 2:
        score += 1
    if len(outline_files) >= 1:
        score += 1
    if len(version_files) >= 1:
        score += 1

    # ---------- Evidence ----------
    evidence.append({
        "draft_files": draft_files,
        "outline_files": outline_files,
        "version_files": version_files,
    })

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




