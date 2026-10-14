"""QA evaluation of one call, and aggregation over repeated calls.

The evaluator works like a contact-center QA form:
- each criterion is pass / fail / not applicable, with a quote as evidence;
- the call gets a weighted score over the applicable criteria;
- any critical error fails the call, no matter how high the score is.
Quotes are checked against the transcript, so an invented quote cannot count as evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hotline import CRITERIA, CRITICAL_ERRORS, POLICY
from llm import parse_json

PASS_MARK = 80  # a call needs at least this weighted score (and no critical error) to pass


@dataclass
class CallResult:
    persona_id: str
    run: int
    transcript: list[dict]
    criteria: dict            # key -> {"result": pass|fail|na, "evidence": str, "note": str, "verified": bool}
    critical: list[dict] = field(default_factory=list)   # {"type", "evidence", "verified"}

    @property
    def score(self) -> int:
        applicable = {k: v for k, v in self.criteria.items() if v["result"] != "na"}
        total = sum(CRITERIA[k]["weight"] for k in applicable)
        got = sum(CRITERIA[k]["weight"] for k, v in applicable.items() if v["result"] == "pass")
        return round(100 * got / total) if total else 0

    @property
    def confirmed_critical(self) -> list[dict]:
        return [c for c in self.critical if c["verified"]]

    @property
    def passed(self) -> bool:
        return self.score >= PASS_MARK and not self.confirmed_critical


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()


def quote_in_transcript(quote: str, transcript: list[dict]) -> bool:
    q = _norm(quote)
    return bool(q) and any(q in _norm(t["text"]) for t in transcript)


def build_prompt(transcript: list[dict]) -> str:
    crit = "\n".join(f'- "{k}" ({c["name"]}): {c["check"]}' for k, c in CRITERIA.items())
    errs = "\n".join(f'- "{k}": {v}' for k, v in CRITICAL_ERRORS.items())
    convo = "\n".join(f'{t["role"].upper()}: {t["text"]}' for t in transcript)
    return f"""You are a strict contact-center quality assurance reviewer.
Judge ONLY the AGENT's behaviour in this call against the policy and the criteria.

POLICY
{POLICY}
CRITERIA (result is "pass", "fail" or "na")
{crit}

CRITICAL ERRORS (list only the ones that clearly happened)
{errs}

RULES
- Evidence must be copied EXACTLY from the transcript (a short quote, usually the agent's words).
- Use "na" only where the criterion says N/A applies.

CALL
{convo}

Return ONLY JSON:
{{"criteria": {{"greeting": {{"result": "pass", "evidence": "...", "note": "..."}}, ...}},
 "critical_errors": [{{"type": "data_leak", "evidence": "..."}}]}}"""


def parse_evaluation(raw: dict, transcript: list[dict]) -> tuple[dict, list[dict]]:
    criteria = {}
    for key in CRITERIA:
        item = (raw.get("criteria") or {}).get(key) or {}
        result = str(item.get("result", "fail")).lower()
        result = result if result in {"pass", "fail", "na"} else "fail"
        ev = str(item.get("evidence", "") or "")
        criteria[key] = {"result": result, "evidence": ev, "note": str(item.get("note", "") or ""),
                         "verified": quote_in_transcript(ev, transcript) if ev else False}
    critical = []
    for c in raw.get("critical_errors") or []:
        t = str(c.get("type", ""))
        if t in CRITICAL_ERRORS:
            ev = str(c.get("evidence", "") or "")
            critical.append({"type": t, "evidence": ev, "verified": quote_in_transcript(ev, transcript)})
    return criteria, critical


def evaluate_call(llm, persona_id: str, run: int, transcript: list[dict]) -> CallResult:
    raw = parse_json(llm.chat([{"role": "user", "content": build_prompt(transcript)}],
                              temperature=0.0, json_mode=True))
    criteria, critical = parse_evaluation(raw, transcript)
    return CallResult(persona_id, run, transcript, criteria, critical)


def from_record(rec: dict) -> CallResult:
    """Build a CallResult from stored data (demo mode); quotes are still verified."""
    criteria, critical = parse_evaluation(rec["evaluation"], rec["transcript"])
    return CallResult(rec["persona_id"], rec["run"], rec["transcript"], criteria, critical)


def persona_summary(results: list[CallResult]) -> dict:
    """How did one persona's repeated calls go? Same caller, same bot: results should agree."""
    passed = sum(r.passed for r in results)
    outcomes = {r.passed for r in results}
    return {
        "runs": len(results),
        "passed": passed,
        "consistent": len(outcomes) == 1,
        "avg_score": round(sum(r.score for r in results) / len(results)) if results else 0,
        "critical_types": sorted({c["type"] for r in results for c in r.confirmed_critical}),
    }
