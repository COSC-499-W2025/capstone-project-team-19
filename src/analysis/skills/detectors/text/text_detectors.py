import re
from collections import Counter
from typing import Any, Dict, Optional

from nltk.corpus import stopwords
from src.analysis.text_individual.alt_analyze import analyze_linguistic_complexity

# Feedback plumbing
try:
    from src.db.project_feedback import upsert_project_feedback  
except Exception:
    upsert_project_feedback = None


def _emit_feedback(
    feedback_ctx: Optional[Dict[str, Any]],
    *,
    skill_name: str,
    file_name: str,
    criterion_key: str,
    criterion_label: str,
    expected: str,
    observed: Dict[str, Any],
    suggestion: str,
) -> None:
    if not feedback_ctx:
        return

    # Preferred: caller provides a callback that writes to DB (keeps detectors decoupled).
    cb = feedback_ctx.get("add_feedback")
    if callable(cb):
        cb(
            skill_name,
            file_name,
            criterion_key,
            criterion_label,
            expected,
            observed,
            suggestion,
        )
        return

    # Fallback: write directly if helper exists and ctx has conn/user/project.
    if upsert_project_feedback is None:
        return

    conn = feedback_ctx.get("conn")
    user_id = feedback_ctx.get("user_id")
    project_name = feedback_ctx.get("project_name")
    project_type = feedback_ctx.get("project_type") or "text"

    if conn is None or user_id is None or not project_name:
        return

    upsert_project_feedback(
        conn=conn,
        user_id=int(user_id),
        project_name=str(project_name),
        project_type=str(project_type),
        skill_name=str(skill_name),
        file_name=str(file_name or ""),
        criterion_key=str(criterion_key),
        criterion_label=str(criterion_label),
        expected=str(expected),
        observed=observed or {},
        suggestion=str(suggestion),
    )


# ---------------------------------------------------------------------
# 1) CLARITY
# ---------------------------------------------------------------------
def detect_sentence_clarity(file_text: str, file_name: str, feedback_ctx=None):
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
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[\.!?])\s+", file_text.strip())
        if s.strip()
    ]

    if not sentences:
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.no_sentences",
            criterion_label="Include enough text for clarity analysis",
            expected="At least 1 sentence",
            observed={"sentence_count": 0},
            suggestion="Provide more written content (at least a few sentences) to allow clarity checks.",
        )
        return {"score": 0, "evidence": {}}

    total_criteria = 5
    score = 5

    evidence = {
        "fragments_runons": [],
        "subj_verb_agreement": [],
        "misplaced_modifiers": [],
        "wordiness": [],
        "pronoun_homophone": [],
    }

    # --- Helper heuristic functions ---
    def is_runon_or_fragment(s: str) -> bool:
        words = s.split()
        if len(words) < 4 or not re.search(r"\b(is|are|was|were|has|had|does|do|did)\b", s, re.I):
            return True
        if len(words) > 40 and ("," not in s and ";" not in s):
            return True
        return False

    def has_subj_verb_error(s: str) -> bool:
        if re.search(r"\b(people|students|data|results)\s+is\b", s, re.I):
            return True
        if re.search(r"\b(each|every)\s+\w+\s+are\b", s, re.I):
            return True
        return False

    def is_misplaced_modifier(s: str) -> bool:
        return bool(re.match(r"^(Having|Being|While)\s+\w+", s))

    def is_wordy(s: str) -> bool:
        words = s.split()
        filler = re.search(r"\b(very|really|in addition|furthermore)\b", s, re.I)
        return len(words) > 22 or bool(filler)

    def has_pronoun_homophone_issue(s: str) -> bool:
        if re.search(r"\b(it|this|that)\b.*\b(it|this|that)\b", s, re.I):
            return True
        if re.search(r"\b(their|there|they\'re)\b", s, re.I):
            return True
        if re.search(r"\b(its|it\'s)\b", s, re.I):
            return True
        return False

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

    threshold_5 = max(1, int(len(sentences) * 0.05))
    threshold_10 = max(1, int(len(sentences) * 0.10))

    # C1 fragments/run-ons
    if len(evidence["fragments_runons"]) <= threshold_5:
        score -= 1
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.fragments_runons",
            criterion_label="Limit fragments and run-on sentences",
            expected=f"≤ {threshold_5} flagged sentences (~5% of total)",
            observed={
                "flagged": len(evidence["fragments_runons"]),
                "threshold": threshold_5,
                "total_sentences": len(sentences),
            },
            suggestion="Split long sentences, add punctuation, and ensure each sentence has a clear subject + verb.",
        )

    # C2 subject-verb agreement
    if len(evidence["subj_verb_agreement"]) == 0:
        score -= 1
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.subject_verb_agreement",
            criterion_label="Avoid subject–verb agreement errors",
            expected="0 agreement errors",
            observed={"flagged": len(evidence["subj_verb_agreement"])},
            suggestion="Fix singular/plural mismatches (e.g., 'data are', 'each X is').",
        )

    # C3 misplaced modifiers
    if len(evidence["misplaced_modifiers"]) <= threshold_5:
        score -= 1
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.misplaced_modifiers",
            criterion_label="Avoid misplaced/dangling modifiers",
            expected=f"≤ {threshold_5} flagged sentences (~5% of total)",
            observed={
                "flagged": len(evidence["misplaced_modifiers"]),
                "threshold": threshold_5,
                "total_sentences": len(sentences),
            },
            suggestion="Rewrite dangling participles so the subject performing the action is explicit.",
        )

    # C4 wordiness
    if len(evidence["wordiness"]) <= threshold_10:
        score -= 1
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.wordiness",
            criterion_label="Reduce wordiness and filler words",
            expected=f"≤ {threshold_10} flagged sentences (~10% of total)",
            observed={
                "flagged": len(evidence["wordiness"]),
                "threshold": threshold_10,
                "total_sentences": len(sentences),
            },
            suggestion="Remove filler (very/really/furthermore) and shorten sentences over ~22 words when possible.",
        )

    # C5 pronoun/homophone issues
    if len(evidence["pronoun_homophone"]) <= threshold_5:
        score -= 1
        _emit_feedback(
            feedback_ctx,
            skill_name="clarity",
            file_name=file_name,
            criterion_key="clarity.pronoun_homophone",
            criterion_label="Avoid vague pronouns and homophone mixups",
            expected=f"≤ {threshold_5} flagged sentences (~5% of total)",
            observed={
                "flagged": len(evidence["pronoun_homophone"]),
                "threshold": threshold_5,
                "total_sentences": len(sentences),
            },
            suggestion="Replace vague 'this/it/that' with a specific noun and proofread their/there/they're and its/it's.",
        )

    return {"score": score / total_criteria, "evidence": evidence}


# ---------------------------------------------------------------------
# 2) STRUCTURE
# ---------------------------------------------------------------------
def detect_paragraph_structure(file_text: str, file_name: str, feedback_ctx=None):
    """
    Criteria (max 4 points):
      1. >= 3 paragraphs
      2. >= 2 paragraphs contain >= 2 sentences
      3. Paragraphs not excessively long (< 250 words)
      4. Paragraph-level transitions detected (keywords)
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", file_text) if p.strip()]
    if not paragraphs:
        _emit_feedback(
            feedback_ctx,
            skill_name="structure",
            file_name=file_name,
            criterion_key="structure.no_paragraphs",
            criterion_label="Include paragraph breaks",
            expected="At least 1 paragraph (separated by blank lines)",
            observed={"paragraph_count": 0},
            suggestion="Separate content into paragraphs using blank lines.",
        )
        return {"score": 0, "evidence": []}

    evidence = []
    score = 0
    total = 4

    # C1: >= 3 paragraphs
    if len(paragraphs) >= 3:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="structure",
            file_name=file_name,
            criterion_key="structure.paragraph_count",
            criterion_label="Use multiple paragraphs",
            expected="≥ 3 paragraphs",
            observed={"paragraph_count": len(paragraphs)},
            suggestion="Break the writing into at least 3 paragraphs (intro/body/conclusion style).",
        )

    # C2: >= 2 paragraphs have >= 2 sentences
    strong = 0
    sent_counts = []
    for p in paragraphs:
        sent_count = len(re.split(r"[.!?]+\s+", p.strip())) if p.strip() else 0
        sent_counts.append(sent_count)
        evidence.append({"paragraph_preview": p[:80], "sentence_count": sent_count})
        if sent_count >= 2:
            strong += 1

    if strong >= 2:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="structure",
            file_name=file_name,
            criterion_key="structure.strong_paragraphs",
            criterion_label="Develop paragraphs with multiple sentences",
            expected="≥ 2 paragraphs with ≥ 2 sentences each",
            observed={"strong_paragraphs": strong, "sentence_counts": sent_counts},
            suggestion="Expand at least 2 paragraphs so each contains 2+ complete sentences (topic + support).",
        )

    # C3: each paragraph < 250 words
    lengths = [len(p.split()) for p in paragraphs]
    if all(wc < 250 for wc in lengths):
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="structure",
            file_name=file_name,
            criterion_key="structure.paragraph_length",
            criterion_label="Avoid overly long paragraphs",
            expected="All paragraphs < 250 words",
            observed={"paragraph_word_counts": lengths, "max_words": max(lengths) if lengths else 0},
            suggestion="Split long paragraphs into smaller ones; aim for one main idea per paragraph.",
        )

    # C4: transitions
    transitions = ["however", "in addition", "moreover", "furthermore", "overall"]
    text_lower = file_text.lower()
    found_transitions = [t for t in transitions if t in text_lower]
    if found_transitions:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="structure",
            file_name=file_name,
            criterion_key="structure.transitions",
            criterion_label="Use paragraph transitions",
            expected="At least 1 transition word (e.g., however, overall)",
            observed={"found": found_transitions},
            suggestion="Add transition words to connect ideas (e.g., 'However', 'In addition', 'Overall').",
        )

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 3) VOCABULARY
# ---------------------------------------------------------------------
def detect_vocabulary_diversity(file_text: str, file_name: str, feedback_ctx=None):
    """
    Criteria (max 4 points):
      1. lexical_diversity >= 0.35
      2. lexical_diversity >= 0.45
      3. FK grade >= 10
      4. FK grade >= 13
    """
    metrics = analyze_linguistic_complexity(file_text)
    lex = float(metrics.get("lexical_diversity", 0) or 0)
    grade = float(metrics.get("flesch_kincaid_grade", 0) or 0)

    score = 0
    total = 4

    if lex >= 0.35:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="vocabulary",
            file_name=file_name,
            criterion_key="vocabulary.lex_div_035",
            criterion_label="Increase lexical diversity (baseline)",
            expected="lexical_diversity ≥ 0.35",
            observed={"lexical_diversity": lex},
            suggestion="Vary word choice and reduce repeated terms by using precise alternatives.",
        )

    if lex >= 0.45:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="vocabulary",
            file_name=file_name,
            criterion_key="vocabulary.lex_div_045",
            criterion_label="Increase lexical diversity (strong)",
            expected="lexical_diversity ≥ 0.45",
            observed={"lexical_diversity": lex},
            suggestion="Use more specific nouns/verbs and avoid repeating the same adjectives and sentence frames.",
        )

    if grade >= 10:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="vocabulary",
            file_name=file_name,
            criterion_key="vocabulary.fk_10",
            criterion_label="Increase academic reading level (baseline)",
            expected="Flesch–Kincaid grade ≥ 10",
            observed={"FK_grade": grade},
            suggestion="Use clearer academic phrasing and add precise terminology where appropriate.",
        )

    if grade >= 13:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="vocabulary",
            file_name=file_name,
            criterion_key="vocabulary.fk_13",
            criterion_label="Increase academic reading level (strong)",
            expected="Flesch–Kincaid grade ≥ 13",
            observed={"FK_grade": grade},
            suggestion="Strengthen sentence complexity carefully (compound/complex sentences) while staying clear.",
        )

    return {
        "score": score / total,
        "evidence": [{
            "lexical_diversity": lex,
            "FK_grade": grade,
            "reading_level": metrics.get("reading_level"),
        }],
    }


# ---------------------------------------------------------------------
# 4) ARGUMENTATION
# ---------------------------------------------------------------------
def detect_argument_structure(file_text: str, file_name: str, feedback_ctx=None):
    """
    Criteria (max 4 points):
      1. 1+ claim markers
      2. 1+ evidence markers
      3. 1+ reasoning terms
      4. 1+ conclusion markers
    """
    text_lower = file_text.lower()

    claim_words = ["i argue", "this paper argues", "i propose", "the thesis is", "the point is"]
    evidence_words = ["according to", "the study shows", "data from", "research indicates", "evidence suggests"]
    reasoning_words = ["because", "therefore", "as a result", "thus", "hence", "this implies"]
    conclusion_words = ["in conclusion", "to conclude", "overall", "in sum", "in closing"]

    score = 0
    total = 4
    ev = {}

    # Claims
    found_claims = [w for w in claim_words if w in text_lower]
    ev["claims"] = found_claims
    if found_claims:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="argumentation",
            file_name=file_name,
            criterion_key="argument.claims",
            criterion_label="Include clear claims/thesis statements",
            expected="At least 1 claim marker",
            observed={"found": found_claims},
            suggestion="Add a direct thesis/claim statement (e.g., 'This paper argues that...').",
        )

    # Evidence
    found_evidence = [w for w in evidence_words if w in text_lower]
    ev["evidence"] = found_evidence
    if found_evidence:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="argumentation",
            file_name=file_name,
            criterion_key="argument.evidence",
            criterion_label="Support claims with evidence signals",
            expected="At least 1 evidence marker",
            observed={"found": found_evidence},
            suggestion="Add evidence phrases (e.g., 'According to...', 'Research indicates...') and cite sources/data.",
        )

    # Reasoning
    found_reasoning = [w for w in reasoning_words if w in text_lower]
    ev["reasoning"] = found_reasoning
    if found_reasoning:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="argumentation",
            file_name=file_name,
            criterion_key="argument.reasoning",
            criterion_label="Explain reasoning (cause/effect, inference)",
            expected="At least 1 reasoning term",
            observed={"found": found_reasoning},
            suggestion="Use causal connectors like 'because', 'therefore', 'as a result' to link evidence to claims.",
        )

    # Conclusion
    found_conclusions = [w for w in conclusion_words if w in text_lower]
    ev["conclusions"] = found_conclusions
    if found_conclusions:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="argumentation",
            file_name=file_name,
            criterion_key="argument.conclusion",
            criterion_label="Add a conclusion signal",
            expected="At least 1 conclusion marker",
            observed={"found": found_conclusions},
            suggestion="Add a concluding sentence/paragraph using 'In conclusion' / 'Overall' / 'In sum'.",
        )

    return {"score": score / total, "evidence": [ev]}


# ---------------------------------------------------------------------
# 5) DEPTH
# ---------------------------------------------------------------------
def detect_depth_of_content(file_text: str, file_name: str, feedback_ctx=None):
    """
    Scoring (4 points):
      1. Abstract/conceptual vocabulary (>=5 unique whole-word matches)
      2. Causal/analytical connectors (>=3)
      3. Idea density >= 0.20 AND text >= 80 words
      4. Interpretation phrases (>=2)
    """
    text_lower = file_text.lower()
    words = re.findall(r"[A-Za-z]+", text_lower)
    word_count = len(words)

    if word_count < 80:
        _emit_feedback(
            feedback_ctx,
            skill_name="depth",
            file_name=file_name,
            criterion_key="depth.min_word_count",
            criterion_label="Write enough content for depth analysis",
            expected="≥ 80 words",
            observed={"word_count": word_count},
            suggestion="Add more explanation and analysis so depth signals (connectors, interpretation) can be detected reliably.",
        )
        return {
            "score": 0,
            "evidence": [{
                "reason": "text too short (<80 words for reliable depth analysis)",
                "word_count": word_count,
            }],
        }

    abstract_keywords = [
        "concept", "framework", "theory", "model", "analysis",
        "interpretation", "implication", "assumption",
        "perspective", "principle", "underlying",
    ]

    abstract_count = 0
    for kw in abstract_keywords:
        if re.search(rf"\b{kw}\b", text_lower):
            abstract_count += 1

    connectors = [
        "therefore", "thus", "hence", "consequently",
        "as a result", "this implies", "this suggests",
        "this indicates", "results in", "leads to",
    ]
    connector_hits = [c for c in connectors if c in text_lower]

    stop = set(stopwords.words("english"))
    meaningful = [w for w in words if w not in stop]
    unique_meaningful = set(meaningful)
    idea_density = len(unique_meaningful) / word_count if word_count else 0

    interpretation_patterns = [
        "this shows", "this means", "this demonstrates",
        "we can infer", "the implication is",
    ]
    interpretation_hits = [p for p in interpretation_patterns if p in text_lower]

    score = 0
    total = 4

    if abstract_count >= 5:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="depth",
            file_name=file_name,
            criterion_key="depth.abstract_vocab",
            criterion_label="Use conceptual/analytical vocabulary",
            expected="≥ 5 abstract/concept keywords",
            observed={"abstract_keyword_count": abstract_count},
            suggestion="Add conceptual terms like 'framework', 'analysis', 'implication', and explain underlying principles.",
        )

    if len(connector_hits) >= 3:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="depth",
            file_name=file_name,
            criterion_key="depth.connectors",
            criterion_label="Use analytical connectors",
            expected="≥ 3 analytical connectors (therefore/thus/as a result...)",
            observed={"connector_hits": connector_hits, "count": len(connector_hits)},
            suggestion="Explicitly link ideas using connectors like 'therefore', 'as a result', 'this suggests'.",
        )

    if idea_density >= 0.20:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="depth",
            file_name=file_name,
            criterion_key="depth.idea_density",
            criterion_label="Increase idea density",
            expected="idea_density ≥ 0.20",
            observed={"idea_density": round(idea_density, 3), "word_count": word_count},
            suggestion="Reduce repetition and add more distinct meaningful terms (key concepts, variables, interpretations).",
        )

    if len(interpretation_hits) >= 2:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="depth",
            file_name=file_name,
            criterion_key="depth.interpretation",
            criterion_label="Add interpretation statements",
            expected="≥ 2 interpretation phrases",
            observed={"interpretation_hits": interpretation_hits, "count": len(interpretation_hits)},
            suggestion="Add sentences like 'This shows that...', 'This implies...', 'We can infer that...'.",
        )

    evidence = [{
        "abstract_keyword_count": abstract_count,
        "connector_hits": connector_hits,
        "idea_density": round(idea_density, 3),
        "interpretation_hits": interpretation_hits,
        "word_count": word_count,
    }]

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 6) PROCESS (ITERATION)
# ---------------------------------------------------------------------
# NOTE: \b boundaries fail on underscores (first_draft.docx). Use non-alnum boundaries.
_DRAFT_TOKEN = re.compile(r"(^|[^a-z0-9])(draft|rev|revision)([^a-z0-9]|$)", re.IGNORECASE)
_OUTLINE_TOKEN = re.compile(r"(^|[^a-z0-9])outline([^a-z0-9]|$)", re.IGNORECASE)
_VERSION_TOKEN = re.compile(r"(^|[^a-z0-9])(v\s*\d+|version\s*\d+)([^a-z0-9]|$)", re.IGNORECASE)


def detect_iterative_process(file_text: str, file_name: str, supporting_files=None, feedback_ctx=None):
    """
    Scoring (4 points):
      1. >= 1 draft file
      2. >= 2 drafts
      3. Outline file present
      4. Version markers detected (v# or "version #")
    """
    if not supporting_files:
        # Store a single feedback row indicating iteration evidence missing.
        _emit_feedback(
            feedback_ctx,
            skill_name="process",
            file_name=file_name,
            criterion_key="process.no_supporting_files",
            criterion_label="Provide drafts/outline/version files to show iteration",
            expected="Supporting files include drafts/outline/versioned copies",
            observed={"supporting_files_count": 0},
            suggestion="Include draft files (e.g., first_draft.docx, second_draft.docx), an outline, or versioned filenames (v2).",
        )
        return {"score": 0, "evidence": []}

    score = 0
    total = 4
    evidence = []
    draft_files, version_files, outline_files = [], [], []

    for f in supporting_files:
        fname = f["filename"]
        lower = fname.lower()

        evidence.append({"file": fname})

        if _DRAFT_TOKEN.search(lower):
            draft_files.append(fname)
        if _OUTLINE_TOKEN.search(lower):
            outline_files.append(fname)
        if _VERSION_TOKEN.search(lower):
            version_files.append(fname)

    # C1: >= 1 draft
    if len(draft_files) >= 1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="process",
            file_name=file_name,
            criterion_key="process.has_1_draft",
            criterion_label="Include at least one draft/revision file",
            expected="≥ 1 draft/revision filename",
            observed={"draft_files": draft_files},
            suggestion="Add at least one draft file (e.g., first_draft.docx or revision.docx).",
        )

    # C2: >= 2 drafts
    if len(draft_files) >= 2:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="process",
            file_name=file_name,
            criterion_key="process.has_2_drafts",
            criterion_label="Include multiple drafts to show iteration",
            expected="≥ 2 draft/revision filenames",
            observed={"draft_files": draft_files, "count": len(draft_files)},
            suggestion="Include at least two drafts (e.g., draft_v1.docx and draft_v2.docx).",
        )

    # C3: outline present
    if len(outline_files) >= 1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="process",
            file_name=file_name,
            criterion_key="process.has_outline",
            criterion_label="Include an outline file",
            expected="At least 1 outline filename",
            observed={"outline_files": outline_files},
            suggestion="Include an outline (outline.docx / outline.txt) to show planning.",
        )

    # C4: version markers present
    if len(version_files) >= 1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="process",
            file_name=file_name,
            criterion_key="process.has_version_markers",
            criterion_label="Use version markers in filenames",
            expected="At least 1 file with v2 / version 2",
            observed={"version_files": version_files},
            suggestion="Use version markers like v2/v3 or 'version 2' in filenames (e.g., report_v2.docx).",
        )

    evidence.append({
        "draft_files": draft_files,
        "outline_files": outline_files,
        "version_files": version_files,
    })

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 7) PLANNING
# ---------------------------------------------------------------------
def detect_planning_behavior(file_text: str, file_name: str, supporting_files=None, feedback_ctx=None):
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

    # C1 outline present
    outlines = []
    if supporting_files:
        outlines = [f for f in supporting_files if "outline" in f["filename"].lower()]
        if outlines:
            score += 1
            evidence.extend([{"outline_file": f["filename"]} for f in outlines])
        else:
            _emit_feedback(
                feedback_ctx,
                skill_name="planning",
                file_name=file_name,
                criterion_key="planning.outline",
                criterion_label="Provide an outline file",
                expected="At least 1 outline file",
                observed={"outline_files": []},
                suggestion="Include outline.docx / outline.txt to show upfront planning.",
            )
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="planning",
            file_name=file_name,
            criterion_key="planning.outline_missing_supporting",
            criterion_label="Provide supporting files for planning evidence",
            expected="Supporting files include an outline",
            observed={"supporting_files_count": 0},
            suggestion="Attach an outline file to show planning work (outline.docx / outline.txt).",
        )

    # C2 section markers
    if any(x in text_lower for x in ["introduction", "method", "conclusion", "overview"]):
        score += 1
        evidence.append({"section_markers": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="planning",
            file_name=file_name,
            criterion_key="planning.section_markers",
            criterion_label="Use section structure",
            expected="At least 1 section marker (Introduction/Method/Conclusion/Overview)",
            observed={"found_any": False},
            suggestion="Add clear headings like Introduction, Methods, Results, Conclusion.",
        )

    # C3 bullet lists
    if re.search(r"[-*]\s+\w+", file_text):
        score += 1
        evidence.append({"bullet_list": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="planning",
            file_name=file_name,
            criterion_key="planning.bullets",
            criterion_label="Use bullet lists for planning/organization",
            expected="At least one bullet list item",
            observed={"found_any": False},
            suggestion="Use bullet lists for outlines, key points, or steps to show structure and planning.",
        )

    # C4 numbered lists
    if re.search(r"\d+\.\s+\w+", file_text):
        score += 1
        evidence.append({"numbered_list": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="planning",
            file_name=file_name,
            criterion_key="planning.numbered_lists",
            criterion_label="Use numbered steps where appropriate",
            expected="At least one numbered list item",
            observed={"found_any": False},
            suggestion="Add numbered steps (1., 2., 3.) for procedures, methods, or ordered reasoning.",
        )

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 8) RESEARCH
# ---------------------------------------------------------------------
def detect_evidence_of_research(file_text: str, file_name: str, feedback_ctx=None):
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

    apa = re.findall(r"\([A-Za-z]+, \d{4}\)", text)
    if apa:
        score += 1
        evidence.append({"APA_citations": apa})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.apa_present",
            criterion_label="Include APA-style citations",
            expected="At least 1 APA citation like (Smith, 2020)",
            observed={"apa_count": 0},
            suggestion="Add citations in APA format (Author, Year) where you reference sources.",
        )

    if len(apa) >= 3:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.apa_count_3",
            criterion_label="Use multiple APA citations",
            expected="≥ 3 APA citations",
            observed={"apa_count": len(apa)},
            suggestion="Cite sources consistently throughout the document (aim for 3+ citations if appropriate).",
        )

    mla = re.findall(r"[A-Z][a-zA-Z]+ \d{1,3}", text)
    if mla:
        score += 1
        evidence.append({"MLA_citations": mla})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.mla_present",
            criterion_label="Include MLA-style citations",
            expected="At least 1 MLA citation like (Smith 22) in-text",
            observed={"mla_count": 0},
            suggestion="If using MLA, add citations like 'Smith 22' where you reference sources.",
        )

    if len(mla) >= 3:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.mla_count_3",
            criterion_label="Use multiple MLA citations",
            expected="≥ 3 MLA citations",
            observed={"mla_count": len(mla)},
            suggestion="Add more in-text citations to show evidence and research support.",
        )

    numeric = re.findall(r"\[\d+\]", text)
    if numeric:
        score += 1
        evidence.append({"numeric_citations": numeric})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.numeric_citations",
            criterion_label="Use numeric citation style (if applicable)",
            expected="At least 1 numeric citation like [1]",
            observed={"numeric_count": 0},
            suggestion="If using numeric citations, include references like [1], [2] in the text.",
        )

    if "according to" in lower:
        score += 1
        evidence.append({"phrase": "according to"})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.signal_phrase",
            criterion_label="Use evidence signal phrases",
            expected="Include 'according to' or similar source signal phrasing",
            observed={"found": False},
            suggestion="Add signal phrases like 'According to X (Year)...' to clearly attribute claims to sources.",
        )

    if re.search(r"[A-Z][a-z]+ (argues|notes|claims|states)", text):
        score += 1
        evidence.append({"author_verb_pattern": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.author_verb_pattern",
            criterion_label="Reference authors using author–verb patterns",
            expected="Pattern like 'Smith argues/notes/claims/states'",
            observed={"found": False},
            suggestion="Integrate sources with phrasing like 'Smith argues that...' or 'Jones states...'.",
        )

    research_terms = ["study", "journal", "paper", "research", "dataset"]
    if any(r in lower for r in research_terms):
        score += 1
        evidence.append({"research_terms": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="research",
            file_name=file_name,
            criterion_key="research.research_terms",
            criterion_label="Use research-oriented vocabulary",
            expected="At least 1 term like study/journal/research/dataset",
            observed={"found": False},
            suggestion="Mention research context explicitly (study, journal, paper, dataset) when discussing evidence.",
        )

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 9) DATA COLLECTION (CSV-BASED)
# ---------------------------------------------------------------------
def detect_data_collection(file_text, file_name, supporting_files=None, csv_metadata=None, feedback_ctx=None):
    """
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
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.no_csv",
            criterion_label="Provide CSV data files",
            expected="At least 1 CSV file in submission",
            observed={"csv_files": 0},
            suggestion="Include at least one CSV dataset with headers and multiple rows/columns.",
        )
        return {"score": 0, "evidence": []}

    files = csv_metadata["files"]
    score = 0
    total = 9
    evidence = []

    for f in files:
        evidence.append({
            "file_name": f["file_name"],
            "rows": int(f["row_count"]),
            "cols": int(f["col_count"]),
            "missing_pct": float(f["missing_pct"]),
            "headers": list(f["headers"]),
        })

    any_cols_gt_1 = any(int(f["col_count"]) > 1 for f in files)
    any_cols_gt_3 = any(int(f["col_count"]) > 3 for f in files)
    any_rows_gt_1 = any(int(f["row_count"]) > 1 for f in files)
    any_rows_gt_5 = any(int(f["row_count"]) > 5 for f in files)
    any_miss_lt_50 = any(float(f["missing_pct"]) < 50.0 for f in files)
    any_miss_lt_15 = any(float(f["missing_pct"]) < 15.0 for f in files)
    any_miss_eq_0 = any(float(f["missing_pct"]) == 0.0 for f in files)
    has_growth_trend = bool(csv_metadata.get("growth_trend_present"))

    # C1: at least one CSV
    if len(files) >= 1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.has_csv",
            criterion_label="Include at least one CSV",
            expected="≥ 1 CSV file",
            observed={"csv_count": len(files)},
            suggestion="Attach a CSV file that contains your collected dataset.",
        )

    # C2: >1 column
    if any_cols_gt_1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.cols_gt_1",
            criterion_label="Use multiple columns",
            expected="At least one CSV with > 1 column",
            observed={"max_cols": max(int(f["col_count"]) for f in files)},
            suggestion="Add more variables/fields (multiple columns) with clear headers.",
        )

    # C3: >3 columns
    if any_cols_gt_3:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.cols_gt_3",
            criterion_label="Include richer datasets (more fields)",
            expected="At least one CSV with > 3 columns",
            observed={"max_cols": max(int(f["col_count"]) for f in files)},
            suggestion="Include additional relevant variables (aim for 4+ columns) with meaningful headers.",
        )

    # C4: >1 row
    if any_rows_gt_1:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.rows_gt_1",
            criterion_label="Include more than one observation",
            expected="At least one CSV with > 1 row",
            observed={"max_rows": max(int(f["row_count"]) for f in files)},
            suggestion="Add multiple observations/records; a single row is usually insufficient.",
        )

    # C5: >5 rows
    if any_rows_gt_5:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.rows_gt_5",
            criterion_label="Collect enough observations",
            expected="At least one CSV with > 5 rows",
            observed={"max_rows": max(int(f["row_count"]) for f in files)},
            suggestion="Collect more data points/entries to support meaningful analysis (aim 6+ rows).",
        )

    # C6: missing_pct < 50
    if any_miss_lt_50:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.missing_lt_50",
            criterion_label="Avoid heavily missing datasets",
            expected="At least one CSV with missing_pct < 50%",
            observed={"min_missing_pct": min(float(f["missing_pct"]) for f in files)},
            suggestion="Reduce missing values by cleaning data or ensuring consistent data entry.",
        )

    # C7: missing_pct < 15
    if any_miss_lt_15:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.missing_lt_15",
            criterion_label="Keep missingness low",
            expected="At least one CSV with missing_pct < 15%",
            observed={"min_missing_pct": min(float(f["missing_pct"]) for f in files)},
            suggestion="Clean the dataset (fill/remove missing entries) to keep missingness under 15%.",
        )

    # C8: missing_pct == 0
    if any_miss_eq_0:
        score += 1
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.missing_eq_0",
            criterion_label="Provide at least one complete dataset",
            expected="At least one CSV with missing_pct == 0%",
            observed={"min_missing_pct": min(float(f["missing_pct"]) for f in files)},
            suggestion="Aim to have at least one dataset version with no missing values after cleaning.",
        )

    # C9: growth trend
    if has_growth_trend:
        score += 1
        evidence.append({"growth_trend_present": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_collection",
            file_name=file_name,
            criterion_key="data_collection.growth_trend",
            criterion_label="Include a growth trend signal (if applicable)",
            expected="csv_metadata.growth_trend_present == True",
            observed={"growth_trend_present": False},
            suggestion="Include time/sequence columns (e.g., Day/Week) so growth trends can be detected.",
        )

    return {"score": score / total, "evidence": evidence}


# ---------------------------------------------------------------------
# 10) DATA ANALYSIS
# ---------------------------------------------------------------------
def detect_data_analysis(file_text: str, file_name: str, supporting_files=None, feedback_ctx=None):
    """
    Criteria (max 4 points):
      1. Mentions of results/graph/table/figure
      2. Mentions of statistical terms (correlation/regression)
      3. Mentions of quantitative comparisons (increase/decrease/trend)
      4. Mentions of interpretation ("shows", "indicates", "suggests")
    """
    lower = file_text.lower()
    score = 0
    total = 4
    evidence = []

    if any(k in lower for k in ["result", "graph", "table", "figure"]):
        score += 1
        evidence.append({"visual_reference": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_analysis",
            file_name=file_name,
            criterion_key="data_analysis.visual_reference",
            criterion_label="Reference results/figures/tables",
            expected="Mention result/graph/table/figure",
            observed={"found": False},
            suggestion="Refer to results explicitly (e.g., 'Figure 1 shows...', 'Table 2 indicates...').",
        )

    if any(k in lower for k in ["correlation", "regression"]):
        score += 1
        evidence.append({"stat_terms": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_analysis",
            file_name=file_name,
            criterion_key="data_analysis.stat_terms",
            criterion_label="Use statistical terms",
            expected="Mention correlation/regression (or other statistical analysis terms)",
            observed={"found": False},
            suggestion="Include analysis terminology (correlation, regression, mean, variance, p-value) if appropriate.",
        )

    if any(k in lower for k in ["increase", "decrease", "trend"]):
        score += 1
        evidence.append({"trend_reference": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_analysis",
            file_name=file_name,
            criterion_key="data_analysis.trend_reference",
            criterion_label="Describe quantitative changes/trends",
            expected="Mention increase/decrease/trend",
            observed={"found": False},
            suggestion="Describe patterns quantitatively (e.g., 'increased by', 'decreased', 'shows an upward trend').",
        )

    if any(k in lower for k in ["shows", "indicates", "suggests"]):
        score += 1
        evidence.append({"interpretation": True})
    else:
        _emit_feedback(
            feedback_ctx,
            skill_name="data_analysis",
            file_name=file_name,
            criterion_key="data_analysis.interpretation",
            criterion_label="Interpret results",
            expected="Use interpretation words (shows/indicates/suggests)",
            observed={"found": False},
            suggestion="Add interpretation statements that explain what the results mean (e.g., 'This indicates that...').",
        )

    return {"score": score / total, "evidence": evidence}
