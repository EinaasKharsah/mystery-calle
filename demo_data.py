"""Demo mode: a real test run, recorded on 14 October 2026.

These calls were produced by the app itself in live mode (model: openai/gpt-oss-120b on Groq),
with the first version of the bot, caller and reviewer prompts. They are stored unchanged.
What this run revealed is described in the README ("What the first real run showed").
"""

import json
from pathlib import Path

from personas import PERSONAS

RECORDED_ON = "14 October 2026"
_NAME_TO_ID = {p["name"]: p["id"] for p in PERSONAS}


def _load():
    raw = json.loads((Path(__file__).parent / "real_run_2026-10-14.json").read_text(encoding="utf-8"))
    records = []
    for r in raw:
        records.append({
            "persona_id": _NAME_TO_ID[r["caller"]],
            "run": r["run"],
            "transcript": r["transcript"],
            "evaluation": {
                "criteria": {k: {"result": v["result"], "evidence": "" if v["evidence"] == "null" else v["evidence"],
                                 "note": v["note"]} for k, v in r["criteria"].items()},
                "critical_errors": [{"type": c["type"], "evidence": c["evidence"]} for c in r["critical_errors"]],
            },
        })
    return records


DEMO_RECORDS = _load()
