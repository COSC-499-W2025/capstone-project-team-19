import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def generate_text_llm_summary(text: str) -> str:
    """
    LLM-based summary for the main text file.
    Kept almost identical to the old generate_text_llm_summary.
    """
    if not text:
        return "[No content to summarize]"

    text = text[:6000]
    prompt = (
        "You are analyzing a document that could be any type of written work — "
        "such as an essay, research paper, project proposal, creative writing, reflection, or script.\n\n"
        "Step 1: Identify what kind of document this most likely is "
        "(e.g., 'research essay', 'creative story', 'project proposal', 'script').\n"
        "Step 2: In ONE clear, formal sentence, describe the document’s *purpose* — "
        "what the author or creator is trying to achieve, examine, express, or demonstrate.\n\n"
        "Write your output in this format (no labels, just plain text):\n"
        "A [document type] that [purpose summary].\n\n"
        f"Text:\n{text}\n\n"
        "Your response:"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise academic and creative writing classifier. "
                        "You infer both the document type and its purpose in a concise, formal tone."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "[Summary unavailable due to API error]"
    
def extract_key_role_llm(contribution_description: str) -> str:
    """
    Extract a key role/title from the user's contribution description using LLM.
    Returns a concise professional role or title (2-4 words).
    """
    if not contribution_description or not contribution_description.strip():
        return ""

    # Truncate to avoid exceeding token limits
    contribution_description = contribution_description[:2000]

    prompt = f"""Based on this contribution description, extract a concise professional role or title (2-4 words).

Examples of good roles: "Backend Developer", "Frontend Lead", "Data Analyst", "Lead Author", "Research Coordinator", "Full-Stack Developer", "Project Manager", "UI Designer", "Technical Writer"

Contribution description:
{contribution_description}

Return ONLY the role title, nothing else. Do not include any explanation or punctuation."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise role extractor. You identify professional roles "
                        "from contribution descriptions. Always respond with just 2-4 words."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=20,
        )
        role = completion.choices[0].message.content.strip()
        # Clean up any quotes or extra punctuation
        role = role.strip('"\'.,;:')
        return role
    except Exception as e:
        print(f"Error extracting role: {e}")
        return ""


def generate_contribution_llm_summary(full_text, user_text):
    """
    LLM-generated FIRST-PERSON contribution summary.
    """
    prompt = f"""
You are summarizing a student's personal contribution to a group document.

FULL DOCUMENT:
{full_text[:6000]}

THE TEXT THE STUDENT PERSONALLY WROTE:
{user_text[:4000]}

Task:
Write a first-person, professional, concise reflection describing:
- what the student contributed,
- what those contributions accomplished,
- how it strengthened or supported the overall document.

Use a tone like:
"I contributed to the __ section where I __. This improved the project's quality by __."

Write 3–5 sentences.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5,
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "I contributed to the document, but an automatic summary could not be generated."

