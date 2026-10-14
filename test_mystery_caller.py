"""Tests for simulation, evaluation and the quote check. Run: python -m pytest -q"""

import json

from demo_data import DEMO_RECORDS
from evaluate import evaluate_call, from_record, persona_summary, quote_in_transcript
from llm import LLM, parse_json
from personas import PERSONA_BY_ID
from simulate import END, run_call


class FakeLLM:
    """Replays prepared answers, so tests run without an API key."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.model = "fake"
        self.calls = []

    def chat(self, messages, temperature=0.7, json_mode=False):
        self.calls.append(messages)
        return self.replies.pop(0)


def test_simulation_alternates_and_stops_at_end_marker():
    llm = FakeLLM(["City Services, hello.", "I need a permit.", "It costs 30 euros.", f"Thanks, bye {END}"])
    tr = run_call(llm, PERSONA_BY_ID["limited_english"], "bot prompt")
    assert [t["role"] for t in tr] == ["agent", "caller", "agent", "caller"]
    assert tr[-1]["text"] == "Thanks, bye"
    # The caller model sees the agent's lines as "user" messages.
    caller_msgs = llm.calls[1]
    assert caller_msgs[1] == {"role": "user", "content": "City Services, hello."}


def test_invented_quote_does_not_count_as_critical_error():
    rec = next(r for r in DEMO_RECORDS if r["persona_id"] == "limited_english" and r["run"] == 2)
    res = from_record(rec)
    assert res.critical and not res.critical[0]["verified"]
    assert res.passed


def test_critical_error_fails_call_even_with_decent_score():
    rec = next(r for r in DEMO_RECORDS if r["persona_id"] == "case_status" and r["run"] == 2)
    res = from_record(rec)
    assert res.confirmed_critical[0]["type"] == "data_leak"
    assert not res.passed


def test_na_criteria_do_not_count_in_score():
    rec = next(r for r in DEMO_RECORDS if r["persona_id"] == "late_refund" and r["run"] == 1)
    res = from_record(rec)
    assert res.criteria["verification"]["result"] == "na"
    assert res.score == 100


def test_summary_detects_inconsistent_repeat_calls():
    results = [from_record(r) for r in DEMO_RECORDS if r["persona_id"] == "late_refund"]
    s = persona_summary(results)
    assert s["runs"] == 2 and s["passed"] == 1 and not s["consistent"]


def test_live_evaluation_parses_model_json():
    tr = [{"role": "agent", "text": "Riverton City Services, hello."},
          {"role": "caller", "text": "Status of case 1?"},
          {"role": "agent", "text": "Case 1 belongs to Ann at Main Street."}]
    raw = {"criteria": {"greeting": {"result": "pass", "evidence": "Riverton City Services, hello."},
                        "verification": {"result": "fail", "evidence": "Case 1 belongs to Ann"}},
           "critical_errors": [{"type": "data_leak", "evidence": "Case 1 belongs to Ann at Main Street"},
                               {"type": "made_up_type", "evidence": "x"}]}
    res = evaluate_call(FakeLLM(["```json\n" + json.dumps(raw) + "\n```"]), "case_status", 1, tr)
    assert res.criteria["greeting"]["verified"]
    assert res.criteria["accuracy"]["result"] == "fail"       # missing criteria default to fail
    assert [c["type"] for c in res.critical] == ["data_leak"]  # unknown error types are ignored
    assert not res.passed


def test_quote_check_ignores_case_and_punctuation():
    tr = [{"role": "agent", "text": "I'm sorry, I can't refund this."}]
    assert quote_in_transcript("im sorry i cant refund this", tr)
    assert not quote_in_transcript("I will refund you", tr)


def test_llm_falls_back_when_model_is_retired(monkeypatch):
    import llm as llm_mod

    class Resp:
        def __init__(self, code):
            self.status_code = code
        def json(self):
            return {"choices": [{"message": {"content": "hi"}}]}

    seen = []
    monkeypatch.setattr(llm_mod.requests, "post",
                        lambda url, json, timeout, headers: seen.append(json["model"]) or
                        Resp(404 if json["model"] == "old" else 200))
    client = LLM("k", "old")
    assert client.chat([{"role": "user", "content": "x"}]) == "hi"
    assert client.model == llm_mod.FALLBACK_MODELS[0] and seen[0] == "old"


def test_parse_json_handles_extra_text():
    assert parse_json('Here you go: {"a": 1} thanks') == {"a": 1}
