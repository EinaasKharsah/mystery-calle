# Mystery Caller: simulated callers that test a customer-service bot

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
   - critical errors that fail the call immediately: a false promise, sharing data without verification, a missing escalation, legal advice.
5. **Checking the reviewer:** every quote the reviewer gives as evidence is checked against the transcript. If the quote is not in the call, it does not count.
6. **Consistency:** the QA board shows one dot per run, so "same caller, different result" is visible at a glance.
7. **Fix and retest:** edit the bot's instructions, run again, and compare the results before and after.

![Call review](screenshots/call_review.png)

## Why I built it

At my last job I built a deployed AI call quality evaluation feature for a government contact center: script compliance checks, weighted scoring, critical-error detection and a monitoring dashboard. That checked calls *after* they happened. My Master's thesis was about LLMs simulating users, and how their behaviour changes from run to run. Mystery Caller puts the two together: simulated users test a bot *before* real customers meet it, using the same kind of QA rules.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

- **Demo mode** works without any key. It shows eight example calls, written to show what the tool catches: a late-refund promise, a data leak, a missed escalation with legal advice, overly formal language, and one reviewer quote that does not exist in the call.
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
| `demo_data.py` | Example calls for demo mode |
| `ui.py` | The QA board and transcript views |
| `test_mystery_caller.py` | Tests (no API key needed) |

## What I would do next

- Compare the LLM reviewer with human QA reviewers on the same calls.
- Add more callers, for example someone describing an emergency or a caller switching language.
- Run the callers against a real voice bot through speech-to-text and text-to-speech.

All companies, people and cases in this project are fictional.
