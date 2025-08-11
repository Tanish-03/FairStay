import os, json, re
from typing import Dict
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

# LangChain Ollama wrapper (requires langchain-community)
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

ALLOWED = {"harassment", "discrimination", "access", "noise", "property_damage", "other"}
LLM_TIMEOUT_SECONDS = 8  # hard stop so the API never hangs

PROMPT = PromptTemplate.from_template("""
You classify renter complaints and draft a neutral, factual summary.

Complaint:
{complaint}

Return strict JSON with keys:
- category: one of [harassment, discrimination, access, noise, property_damage, other]
- severity: integer 1-5 (5 = most severe)
- summary: <= 60 words, neutral tone

JSON:
""")

def _fallback(complaint: str) -> Dict:
    text = (complaint or "").strip()
    preview = (text[:200] + "...") if len(text) > 200 else text
    return {"category": "other", "severity": 3, "summary": f"Reported issue: {preview}"}

def _normalize_category(cat: str, default_text: str) -> str:
    c = (cat or "").strip().lower()
    return c if c in ALLOWED else "other"

def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    candidate = m.group(0).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            return json.loads(candidate.replace("'", '"'))
        except Exception:
            return None

def _llm_call(prompt: str) -> str:
    llm = Ollama(model=MODEL, temperature=0)
    return llm.invoke(prompt)

def classify_and_summarize(complaint: str) -> Dict:
    """Main entry used by the FastAPI route."""
    try:
        prompt = PROMPT.format(complaint=complaint)

        # Run the LLM with a hard timeout
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_llm_call, prompt)
            try:
                raw = fut.result(timeout=LLM_TIMEOUT_SECONDS)
            except FuturesTimeout:
                return _fallback(complaint)

        data = _extract_json(raw)
        if not data:
            return _fallback(complaint)

        category = _normalize_category(data.get("category", ""), complaint)
        # clamp severity 1..5
        try:
            severity = int(data.get("severity", 3))
        except Exception:
            severity = 3
        severity = max(1, min(severity, 5))

        summary = (str(data.get("summary", "")) or "").strip()
        if not summary:
            summary = _fallback(complaint)["summary"]
        # cap length
        summary = " ".join(summary.split()[:60])[:500]

        return {"category": category, "severity": severity, "summary": summary}
    except Exception:
        return _fallback(complaint)
