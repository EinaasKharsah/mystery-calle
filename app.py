"""Mystery Caller: simulated callers test a customer-service bot; every call gets a QA review.

Run with:  streamlit run app.py
"""

import json
import os
from collections import defaultdict

import streamlit as st

import ui
from demo_data import DEMO_RECORDS
from evaluate import evaluate_call, from_record, persona_summary
from hotline import CRITICAL_ERRORS, DEFAULT_BOT_PROMPT, POLICY
from llm import DEFAULT_MODEL, LLM
from personas import PERSONA_BY_ID, PERSONAS
from simulate import run_call

st.set_page_config(page_title="Mystery Caller – QA for service bots", page_icon="📞", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)

st.session_state.setdefault("results", None)
st.session_state.setdefault("history", [])   # [(label, {persona_id: summary})]
st.session_state.setdefault("bot_prompt", DEFAULT_BOT_PROMPT)

# ---------- settings ----------
with st.sidebar:
    st.markdown("### Settings")
    key = None
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    key = key or os.environ.get("GROQ_API_KEY")
    mode = st.radio("Mode", ["Demo (example calls)", "Live AI (Groq)"], index=1 if key else 0)
    live = mode.startswith("Live")
    if live and not key:
        key = st.text_input("Groq API key", type="password", help="Free key at console.groq.com.")
    runs = st.slider("Calls per caller", 1, 3, 2, disabled=not live,
                     help="Each caller phones more than once. If the bot behaves differently each time, you see it.")
    model = st.text_input("Model", DEFAULT_MODEL, disabled=not live)
    if st.button("Clear results"):
        st.session_state.results = None
        st.session_state.history = []
        st.rerun()

_res = st.session_state.results
st.markdown(ui.masthead([r.passed for r in _res] if _res else None), unsafe_allow_html=True)

tab_setup, tab_results = st.tabs(["Set up the test", "QA results"])

# ---------- setup ----------
with tab_setup:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("#### The bot under test")
        st.caption("A fictional city services hotline. Edit its instructions and run the test again "
                   "to see whether your fix works.")
        st.text_area("Bot instructions", key="bot_prompt", height=300, disabled=not live)
        with st.expander("The policy the bot must follow"):
            st.text(POLICY)
    with right:
        st.markdown("#### The callers")
        st.caption("Each caller has a goal, a temperament and a weak spot to probe.")
        chosen = []
        for p in PERSONAS:
            av, box = st.columns([0.12, 0.88], vertical_alignment="center")
            av.markdown(ui.avatar(p), unsafe_allow_html=True)
            if box.checkbox(f"**{p['name']}**", value=True, key=f"p_{p['id']}"):
                chosen.append(p["id"])
            box.caption(f"{p['summary']} Tests: {p['tests']}")
        with st.expander("Critical errors (fail the call immediately)"):
            for v in CRITICAL_ERRORS.values():
                st.markdown(f"- {v}")

    n_calls = len(chosen) * (runs if live else 2)
    label = (f"Run {n_calls} test calls" if live else "Show the example test calls")
    if st.button(label, type="primary", disabled=not chosen or (live and not key)):
        if not live:
            st.session_state.results = [from_record(r) for r in DEMO_RECORDS if r["persona_id"] in chosen]
        else:
            llm = LLM(key, model)
            results, bar = [], st.progress(0.0, text="Starting calls…")
            done = 0
            try:
                for pid in chosen:
                    for run in range(1, runs + 1):
                        bar.progress(done / n_calls, text=f"{PERSONA_BY_ID[pid]['name']} is calling (run {run})…")
                        tr = run_call(llm, PERSONA_BY_ID[pid], st.session_state.bot_prompt)
                        results.append(evaluate_call(llm, pid, run, tr))
                        done += 1
                bar.progress(1.0, text=f"Done. Model: {llm.model}")
                st.session_state.results = results
            except Exception as e:
                st.error(f"The test stopped: {e}")
        if st.session_state.results:
            groups = defaultdict(list)
            for r in st.session_state.results:
                groups[r.persona_id].append(r)
            label = f"Test {len(st.session_state.history) + 1}"
            st.session_state.history.append((label, {k: persona_summary(v) for k, v in groups.items()}))
            st.rerun()
    if st.session_state.results:
        st.success(f"{len(st.session_state.results)} calls reviewed. Open the QA results tab to see them.")

# ---------- results ----------
with tab_results:
    results = st.session_state.results
    if not results:
        st.info("No calls yet. Set up the test and run it first.")
    else:
        groups = defaultdict(list)
        for r in results:
            groups[r.persona_id].append(r)
        total = len(results)
        passed = sum(r.passed for r in results)
        flips = [PERSONA_BY_ID[k]["name"] for k, v in groups.items() if len({c.passed for c in v}) > 1]
        crit_calls = sum(bool(r.confirmed_critical) for r in results)
        msg = (f'The bot passed <b class="{"good" if passed == total else "bad"}">{passed} of {total}</b> calls. '
               f'<b class="bad">{crit_calls}</b> call{"s" if crit_calls != 1 else ""} had a critical error.')
        if flips and len(flips) == len(groups):
            msg += (' <b class="bad">Every caller</b> got a different result on a repeat call, '
                    'so a single test call per caller would have hidden these problems.')
        elif flips:
            msg += (f' With <b class="bad">{", ".join(flips)}</b>, the same caller got a different result '
                    'on a repeat call, so one test call would not have been enough.')
        st.markdown(f'<div class="mc-lead">{msg}</div>', unsafe_allow_html=True)

        st.markdown(ui.switchboard(results, PERSONA_BY_ID), unsafe_allow_html=True)
        st.markdown("#### Where each call passed or failed")
        st.markdown(ui.board([p for p in PERSONAS if p["id"] in groups], groups), unsafe_allow_html=True)

        crit_all = [(PERSONA_BY_ID[r.persona_id]["name"], r.run, c) for r in results for c in r.critical]
        if crit_all:
            st.markdown("#### Critical errors")
            st.markdown("".join(ui.crit_card(n, run, c) for n, run, c in crit_all), unsafe_allow_html=True)

        if len(st.session_state.history) > 1:
            st.markdown("#### Before and after your changes")
            rows = []
            for lbl, summ in st.session_state.history:
                row = {"Test": lbl}
                for pid, s in summ.items():
                    row[PERSONA_BY_ID[pid]["name"]] = f'{s["passed"]}/{s["runs"]} passed'
                rows.append(row)
            st.dataframe(rows, hide_index=True, width="stretch")

        st.markdown("#### Listen in: read any call")
        options = [f'{PERSONA_BY_ID[r.persona_id]["name"]}, run {r.run} — '
                   f'{"Pass" if r.passed else "Fail"} ({r.score})' for r in results]
        pick = st.selectbox("Call", range(len(results)), format_func=lambda i: options[i])
        call = results[pick]
        a, b = st.columns([1.4, 1], gap="large")
        a.markdown(ui.call_header(call, PERSONA_BY_ID[call.persona_id]) + ui.transcript(call), unsafe_allow_html=True)
        b.markdown(ui.checks(call), unsafe_allow_html=True)
        b.caption("Green marks are evidence for a passed check, red marks for a failed check or critical error. "
                  "Every quote is checked against the call before it counts.")

        report = [{"caller": PERSONA_BY_ID[r.persona_id]["name"], "run": r.run, "score": r.score,
                   "passed": r.passed, "criteria": r.criteria, "critical_errors": r.critical,
                   "transcript": r.transcript} for r in results]
        st.download_button("Download all calls and results (JSON)", json.dumps(report, indent=2),
                           "mystery_caller_results.json")
