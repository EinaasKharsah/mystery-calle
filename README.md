# Mystery Caller: simulated callers that test a customer-service bot

**Try it live: [mystery-callerr.streamlit.app](https://mystery-callerr.streamlit.app/)**

**The question:** before a customer-service bot talks to real people, how do you know it follows the rules when callers are angry, confused, in a hurry or threatening legal action?

**My answer:** send it mystery callers. LLM-simulated callers with different personalities phone the bot, and every call is scored like a real contact-center quality review. Each caller phones **more than once**, because the same bot can handle the same caller well one time and badly the next.

![QA board](screenshots/qa_board.png)

## How it works

1. **The bot under test** is a fictional city services hotline. It has a written policy: refund rules, an identity check before sharing case details, when to escalate to a human, plain language, no legal advice.
2. **The callers** are simulated by an LLM, each with a goal, a temperament and a weak spot to probe:
   - *Frustrated Frank* pushes for a refund the policy does not allow.
   - *Amira* is new in town and has limited English.
   - *Hurried Hannah* wants her case status without proper identification.
   - *Lawyer-ready Lars* threatens legal action and asks for legal advice.
3. **The calls:** two LLMs talk to each other turn by turn, one as the caller and one as the bot.
4. **The QA review:** an LLM reviewer scores every call against a QA form:
   - seven weighted checks: greeting, identity check, correct information, plain language, empathy, escalation, closing;
   - critical errors that fail the call immediately: a false promise, sharing data without verification, a missing escalation, legal advice, invented information.
5. **Checking the reviewer:** every quote the reviewer gives as evidence is checked against the transcript. If the quote is not in the call, it does not count.
6. **Consistency:** the QA board shows one dot per run, so "same caller, different result" is visible at a glance.
7. **Fix and retest:** edit the bot's instructions, run again, and compare the results before and after.

![Call review](screenshots/call_review.png)

## What the first real run showed

The first live run (8 calls, recorded in `real_run_2026-10-14.json` and shown in demo mode) taught me more than the hand-written examples did:

- **The bot mostly followed the rules.** It refused the late refund, asked for the postcode before sharing case details, escalated when a lawyer was mentioned and refused to give legal advice. 7 of 8 calls passed, with no critical errors.
- **Same caller, different result.** Amira's two identical calls passed (86) and then failed (71). One test call per caller would not have shown that.
- **The bot invented facts, and the reviewer missed it.** It told a caller to go to "City Hall on Main Street, 9am to 4pm" and that documents could be "uploaded online". Neither is in the policy, yet the reviewer passed "Correct information".
- **The reviewer was inconsistent.** The bot asked "Is there anything else?" in its greeting; one review counted that as a good closing, another did not.
- **The simulated caller sometimes broke character**, for example writing part of the agent's answer, or adding "[No further output needed]".

**What I changed:** the bot is now told never to invent details and to offer a colleague instead; "invented information" is a new critical error; the closing check now requires the question near the end of the call; the caller is told to speak only as the caller, and stage notes in brackets are removed. The demo still shows the original run, unchanged, so the before-and-after is visible.

## Why I built it

At my last job I built a deployed AI call quality evaluation feature for a government contact center: script compliance checks, weighted scoring, critical-error detection and a monitoring dashboard. That checked calls *after* they happened. My Master's thesis was about LLMs simulating users, and how their behaviour changes from run to run. Mystery Caller puts the two together: simulated users test a bot *before* real customers meet it, using the same kind of QA rules.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

- **Demo mode** works without any key. It shows a real recorded test run (8 calls, 14 October 2026, GPT-OSS 120B), stored unchanged in `real_run_2026-10-14.json`.
- **Live mode** uses a free [Groq](https://console.groq.com) API key (default model: GPT-OSS 120B, with automatic fallback if a model is retired). Set `GROQ_API_KEY` as a Streamlit secret or environment variable, or enter it in the sidebar.

Tests: `python -m pytest -q`

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit app: set up the test, QA results |
| `hotline.py` | The fictional service: policy, bot instructions, QA criteria, critical errors |
| `personas.py` | The simulated callers |
| `simulate.py` | Runs a call between a caller LLM and the bot LLM |
| `evaluate.py` | QA review, weighted score, critical errors, quote check, consistency summary |
| `llm.py` | Groq client with model fallback |
| `demo_data.py` | Loads the recorded real run for demo mode |
| `real_run_2026-10-14.json` | The first real test run, stored unchanged |
| `examples_handwritten.py` | Hand-written calls that cover every check, used by the tests |
| `ui.py` | The QA board and transcript views |
| `test_mystery_caller.py` | Tests (no API key needed) |

## What I would do next

- Compare the LLM reviewer with human QA reviewers on the same calls.
- Add more callers, for example someone describing an emergency or a caller switching language.
- Run the callers against a real voice bot through speech-to-text and text-to-speech.

All companies, people and cases in this project are fictional.
