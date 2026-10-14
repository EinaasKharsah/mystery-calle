"""Visual layer: a QA board where every caller is a row and every check is a column.

Each cell shows one dot per run, so 'same caller, different result' is visible at a glance.
Font: Atkinson Hyperlegible, made for readability, which fits a tool that checks plain language.
"""

from __future__ import annotations

import html
import re

from hotline import CRITERIA, CRITICAL_ERRORS

INK = "#12343B"
PAPER = "#F2F4F1"
PASS = "#2E7D4F"
FAIL = "#B4233C"
NA = "#B8C2C0"
AMBER = "#D89A00"
SWITCH = "#0F2A30"
GREEN_LED = "#4ADE80"
RED_LED = "#FF5A6E"
# One colour per caller, used for avatars everywhere.
PERSONA_COLORS = {"late_refund": "#FFB4A2", "limited_english": "#A0E7E5",
                  "case_status": "#FFE29A", "legal_threat": "#C3B1E1"}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');
html, body, [class*="css"], .stMarkdown, textarea, input, button {{ font-family:'Atkinson Hyperlegible', system-ui, sans-serif !important; }}
.block-container {{ padding-top:3.4rem; max-width:1200px; }}
h1,h2,h3,h4 {{ color:{INK}; letter-spacing:-0.01em; }}

.mc-mast {{ display:flex; align-items:flex-end; gap:1.1rem; flex-wrap:wrap; margin-bottom:1.2rem; }}
.mc-mast .name {{ font-size:2.5rem; font-weight:700; color:{INK}; line-height:1; }}
.mc-mast .name i {{ font-style:normal; display:inline-block; width:.3em; height:.3em; border-radius:50%;
  background:{FAIL}; margin-left:.18em; vertical-align:.55em; }}
.mc-mast .tag {{ color:#47605F; font-size:1.05rem; max-width:52ch; }}

.mc-lead {{ font-size:1.15rem; color:{INK}; max-width:72ch; margin:.2rem 0 1rem; line-height:1.5; }}
.mc-lead b.bad {{ color:{FAIL}; }}
.mc-lead b.good {{ color:{PASS}; }}

/* QA board */
.mc-board {{ width:100%; border-collapse:separate; border-spacing:0; background:#fff; border-radius:12px; overflow:hidden;
  font-size:.95rem; color:{INK}; }}
.mc-board th {{ text-align:left; font-weight:700; padding:.65rem .6rem; background:#E4EAE7; font-size:.85rem; }}
.mc-board th small {{ display:block; font-weight:400; color:#5C716F; }}
.mc-board td {{ padding:.6rem; border-top:1px solid #E4EAE7; vertical-align:middle; }}
.mc-board td.who b {{ display:block; }}
.mc-board td.who span {{ color:#5C716F; font-size:.85rem; }}
.mc-dot {{ display:inline-block; width:14px; height:14px; border-radius:50%; margin-right:4px; vertical-align:middle; }}
.mc-dot.pass {{ background:{PASS}; }}
.mc-dot.fail {{ background:{FAIL}; }}
.mc-dot.na {{ background:transparent; box-shadow:inset 0 0 0 2px {NA}; }}
.mc-tile {{ display:inline-block; padding:.18rem .5rem; border-radius:6px; font-weight:700; font-size:.82rem; margin-right:4px; color:#fff; }}
.mc-tile.pass {{ background:{PASS}; }}
.mc-tile.fail {{ background:{FAIL}; }}
.mc-flip {{ color:{AMBER}; font-weight:700; font-size:.85rem; white-space:nowrap; }}
.mc-steady {{ color:#5C716F; font-size:.85rem; }}
.mc-legend {{ font-size:.85rem; color:#47605F; margin:.5rem 0 0; }}

/* critical errors */
.mc-crit {{ background:#fff; border-left:6px solid {FAIL}; border-radius:6px 10px 10px 6px; padding:.75rem 1rem; margin:.5rem 0; color:{INK}; }}
.mc-crit b {{ color:{FAIL}; }}
.mc-crit q {{ font-style:italic; }}
.mc-crit.unconfirmed {{ border-left-color:{NA}; opacity:.85; }}
.mc-crit.unconfirmed b {{ color:#5C716F; }}

/* transcript */
.mc-call {{ display:flex; flex-direction:column; gap:.45rem; max-width:760px; }}
.mc-turn {{ max-width:80%; padding:.55rem .8rem; border-radius:12px; line-height:1.45; color:{INK}; }}
.mc-turn.agent {{ background:#fff; align-self:flex-start; border-top-left-radius:3px; }}
.mc-turn.caller {{ background:#DCE8E4; align-self:flex-end; border-top-right-radius:3px; }}
.mc-turn small {{ display:block; color:#5C716F; font-size:.75rem; margin-bottom:.1rem; }}
.mc-turn mark {{ padding:0 .12em; border-radius:3px; }}
.mc-turn mark.good {{ background:#CDE9D6; }}
.mc-turn mark.bad {{ background:#F6CBD3; }}
.mc-checks {{ font-size:.92rem; color:{INK}; }}
.mc-checks div {{ margin:.2rem 0; }}

.stButton button[kind="primary"] {{ background:{INK}; border-color:{INK}; }}
button:focus-visible, textarea:focus-visible {{ outline:3px solid {AMBER} !important; outline-offset:2px; }}
/* masthead band */
.mc-band {{ background:{SWITCH}; border-radius:18px; padding:1.5rem 1.6rem 1.3rem; margin-bottom:1.3rem; color:#E6EFEC;
  background-image: radial-gradient(circle at 92% 18%, rgba(255,255,255,.07) 0 22%, transparent 23%); }}
.mc-band .name {{ font-size:2.6rem; font-weight:700; line-height:1; color:#fff; letter-spacing:-0.02em; }}
.mc-band .name i {{ font-style:normal; display:inline-block; width:.28em; height:.28em; border-radius:50%; background:{RED_LED};
  margin-left:.15em; vertical-align:.55em; box-shadow:0 0 12px {RED_LED}; animation: mc-rec 1.6s ease-in-out 3; }}
.mc-band .tag {{ color:#B9CCC7; font-size:1.05rem; margin-top:.5rem; max-width:60ch; }}
.mc-band .lines {{ display:flex; gap:.45rem; margin-top:1rem; }}
.mc-band .lines span {{ width:34px; height:6px; border-radius:3px; background:#2C5158; }}
.mc-band .lines span.on {{ background:{GREEN_LED}; box-shadow:0 0 8px {GREEN_LED}; }}
@keyframes mc-rec {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.25; }} }}

/* switchboard: one lit line per test call */
.mc-switch {{ background:{SWITCH}; border-radius:18px; padding:1.1rem; display:grid;
  grid-template-columns:repeat(auto-fill, minmax(205px, 1fr)); gap:.7rem; margin:.4rem 0 1.4rem; }}
.mc-line {{ background:#173D44; border-radius:12px; padding:.85rem .9rem .8rem; color:#E6EFEC; position:relative; overflow:hidden; }}
.mc-line .top {{ display:flex; align-items:center; gap:.55rem; }}
.mc-line .who {{ font-weight:700; font-size:.95rem; line-height:1.15; }}
.mc-line .who small {{ display:block; font-weight:400; color:#9DB5AF; font-size:.78rem; }}
.mc-line .led {{ position:absolute; top:.85rem; right:.9rem; width:11px; height:11px; border-radius:50%; }}
.mc-line .led.pass {{ background:{GREEN_LED}; box-shadow:0 0 10px {GREEN_LED}; }}
.mc-line .led.fail {{ background:{RED_LED}; box-shadow:0 0 10px {RED_LED}; animation: mc-rec 1.2s ease-in-out 2; }}
.mc-line .score {{ font-size:2.1rem; font-weight:700; margin-top:.55rem; line-height:1; }}
.mc-line .score small {{ font-size:.85rem; color:#9DB5AF; font-weight:400; }}
.mc-line .why {{ font-size:.8rem; color:#F3B4BF; margin-top:.35rem; min-height:2.3em; padding-right:3.6rem; }}
.mc-line .why.ok {{ color:#9FD9B5; }}
.mc-line .stamp {{ position:absolute; right:.6rem; bottom:.55rem; transform:rotate(-9deg); border:2.5px solid {RED_LED};
  color:{RED_LED}; font-weight:700; padding:.05rem .45rem; border-radius:6px; font-size:.95rem; opacity:.9; }}
.mc-line .stamp.ok {{ border-color:{GREEN_LED}; color:{GREEN_LED}; }}

/* caller avatars */
.mc-av {{ display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:50%;
  font-weight:700; font-size:.85rem; color:{SWITCH}; flex:none; }}

/* call header above a transcript */
.mc-callhead {{ display:flex; align-items:center; gap:.7rem; background:{SWITCH}; color:#E6EFEC; border-radius:14px;
  padding:.75rem 1rem; margin-bottom:.8rem; max-width:760px; position:relative; }}
.mc-callhead b {{ font-size:1.05rem; }}
.mc-callhead small {{ color:#9DB5AF; display:block; }}
.mc-callhead .stamp {{ margin-left:auto; transform:rotate(-7deg); border:2.5px solid {RED_LED}; color:{RED_LED};
  font-weight:700; padding:.1rem .55rem; border-radius:6px; }}
.mc-callhead .stamp.ok {{ border-color:{GREEN_LED}; color:{GREEN_LED}; }}
@media (prefers-reduced-motion: reduce) {{ .mc-band .name i, .mc-line .led.fail {{ animation:none; }} }}

</style>
"""


def masthead(lines: list[bool] | None = None) -> str:
    """Dark band with the name, a recording light, and one indicator per test call."""
    ind = ""
    if lines:
        ind = '<div class="lines">' + "".join(f'<span class="{"on" if ok else ""}"></span>' for ok in lines) + "</div>"
    return ('<div class="mc-band"><div class="name">Mystery Caller<i></i></div>'
            '<div class="tag">Simulated callers phone your service bot and try to break it. '
            'Every call is scored like a real contact-center QA review.</div>' + ind + '</div>')


def avatar(persona: dict) -> str:
    initials = "".join(w[0] for w in persona["name"].replace(",", "").split()[:2]).upper()
    return f'<span class="mc-av" style="background:{PERSONA_COLORS.get(persona["id"], "#ddd")}">{initials}</span>'


def switchboard(calls, persona_by_id) -> str:
    """The bold element: every test call as a lit phone line with its score and verdict."""
    cards = []
    for c in calls:
        p = persona_by_id[c.persona_id]
        if c.confirmed_critical:
            why = html.escape(CRITICAL_ERRORS[c.confirmed_critical[0]["type"]].split(" (")[0].rstrip("."))
            why_cls = "why"
        elif not c.passed:
            why, why_cls = "Below 80 points", "why"
        else:
            why, why_cls = "Clean call", "why ok"
        state = "pass" if c.passed else "fail"
        stamp = '<span class="stamp ok">Pass</span>' if c.passed else '<span class="stamp">Fail</span>'
        cards.append(f'<div class="mc-line"><span class="led {state}"></span>'
                     f'<div class="top">{avatar(p)}<div class="who">{html.escape(p["name"])}'
                     f'<small>Call {c.run}</small></div></div>'
                     f'<div class="score">{c.score}<small> / 100</small></div>'
                     f'<div class="{why_cls}">{why}</div>{stamp}</div>')
    return f'<div class="mc-switch">{"".join(cards)}</div>'


def call_header(call, persona) -> str:
    stamp = '<span class="stamp ok">Pass</span>' if call.passed else '<span class="stamp">Fail</span>'
    return (f'<div class="mc-callhead">{avatar(persona)}<div><b>{html.escape(persona["name"])}, call {call.run}</b>'
            f'<small>{html.escape(persona["tests"])}</small></div>{stamp}</div>')


def dots(results_for_criterion: list[str]) -> str:
    return "".join(f'<span class="mc-dot {r}" title="{r}"></span>' for r in results_for_criterion)


def board(personas: list[dict], by_persona: dict) -> str:
    head = "".join(f'<th>{html.escape(c["name"])}<small>{c["weight"]} pts</small></th>' for c in CRITERIA.values())
    rows = []
    for p in personas:
        calls = by_persona.get(p["id"], [])
        if not calls:
            continue
        tiles = "".join(f'<span class="mc-tile {"pass" if c.passed else "fail"}">'
                        f'{"Pass" if c.passed else "Fail"} {c.score}</span>' for c in calls)
        outcomes = {c.passed for c in calls}
        flip = ('<div class="mc-flip">Different result on the same call</div>' if len(outcomes) > 1
                else f'<div class="mc-steady">Same result in all {len(calls)} runs</div>' if len(calls) > 1 else "")
        cells = "".join(f'<td>{dots([c.criteria[k]["result"] for c in calls])}</td>' for k in CRITERIA)
        rows.append(f'<tr><td class="who"><div style="display:flex;gap:.55rem;align-items:flex-start">{avatar(p)}<div><b>{html.escape(p["name"])}</b><span>{html.escape(p["summary"])}</span></div></div></td>'
                    f'<td>{tiles}{flip}</td>{cells}</tr>')
    return (f'<div style="overflow-x:auto"><table class="mc-board" style="min-width:860px"><tr><th>Caller</th><th>Calls</th>{head}</tr>{"".join(rows)}</table></div>'
            '<div class="mc-legend"><span class="mc-dot pass"></span>pass &nbsp; <span class="mc-dot fail"></span>fail '
            '&nbsp; <span class="mc-dot na"></span>not needed in this call &nbsp;·&nbsp; one dot per run. '
            'A call passes with 80 points or more and no critical error.</div>')


def crit_card(persona_name: str, run: int, c: dict) -> str:
    cls = "" if c["verified"] else " unconfirmed"
    label = CRITICAL_ERRORS[c["type"]]
    status = ("" if c["verified"] else
              " The quote the reviewer gave is not in the transcript, so this error is not counted.")
    return (f'<div class="mc-crit{cls}"><b>{html.escape(persona_name)}, run {run}:</b> {html.escape(label)}'
            f'<br><q>{html.escape(c["evidence"])}</q>{status}</div>')


def _pattern(quote: str):
    words = re.findall(r"\w+", quote)
    return re.compile(r"\W+".join(re.escape(w) for w in words), re.IGNORECASE) if words else None


def transcript(call) -> str:
    good = [v["evidence"] for v in call.criteria.values() if v["result"] == "pass" and v["verified"]]
    bad = [v["evidence"] for v in call.criteria.values() if v["result"] == "fail" and v["verified"]]
    bad += [c["evidence"] for c in call.critical if c["verified"]]
    turns = []
    for t in call.transcript:
        text = t["text"]
        spans = []
        for q, cls in [(q, "bad") for q in bad] + [(q, "good") for q in good]:
            pat = _pattern(q)
            m = pat.search(text) if pat else None
            if m and not any(m.start() < e and s < m.end() for s, e, _ in spans):
                spans.append((m.start(), m.end(), cls))
        spans.sort()
        out, pos = [], 0
        for s, e, cls in spans:
            out.append(html.escape(text[pos:s]))
            out.append(f'<mark class="{cls}">{html.escape(text[s:e])}</mark>')
            pos = e
        out.append(html.escape(text[pos:]))
        who = "Bot" if t["role"] == "agent" else "Caller"
        turns.append(f'<div class="mc-turn {t["role"]}"><small>{who}</small>{"".join(out)}</div>')
    return f'<div class="mc-call">{"".join(turns)}</div>'


def checks(call) -> str:
    icon = {"pass": "✅", "fail": "❌", "na": "–"}
    rows = []
    for k, c in CRITERIA.items():
        v = call.criteria[k]
        note = html.escape(v["note"]) if v["note"] else ""
        unv = " <i>(quote not found in the call, ignored)</i>" if v["evidence"] and not v["verified"] else ""
        rows.append(f'<div>{icon[v["result"]]} <b>{html.escape(c["name"])}</b> — {note}{unv}</div>')
    return f'<div class="mc-checks">{"".join(rows)}</div>'
