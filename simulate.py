"""Run a phone conversation between a simulated caller and the bot under test.

Two LLMs talk to each other: one plays the caller (persona), one plays the agent
(the bot under test, with its own system prompt). Each sees the conversation from
its own side.
"""

from __future__ import annotations

import re

from hotline import SERVICE_NAME

END = "[END]"

CALLER_RULES = f"""You are a caller phoning the {SERVICE_NAME} hotline. Stay in character.
Write only what YOU, the caller, say: 1-3 short sentences. Never write the agent's words,
never answer your own questions, and never add notes, actions or text in brackets.
When your issue is solved, or you give up, or the agent ends the call, say goodbye and add {END}."""


def clean_caller_text(text: str) -> str:
    """Remove stage notes like "[No further output needed]" that a model sometimes adds (keeps the END marker)."""
    return re.sub(r"\[(?!END\])[^\]]*\]", "", text).strip()


def _caller_view(transcript):
    # From the caller's side, the agent's lines are the "user" and the caller's own lines are "assistant".
    return [{"role": "user" if t["role"] == "agent" else "assistant", "content": t["text"]} for t in transcript]


def _agent_view(transcript):
    return [{"role": "user" if t["role"] == "caller" else "assistant", "content": t["text"]} for t in transcript]


def run_call(llm, persona: dict, bot_prompt: str, max_turns: int = 8) -> list[dict]:
    """Return the transcript as a list of {"role": "agent" | "caller", "text": ...}."""
    transcript: list[dict] = []
    caller_system = CALLER_RULES + "\n\nYour character:\n" + persona["prompt"]

    # The agent picks up the phone first.
    opening = llm.chat([{"role": "system", "content": bot_prompt},
                        {"role": "user", "content": "(The phone rings. You pick up.)"}])
    transcript.append({"role": "agent", "text": opening.strip()})

    for _ in range(max_turns):
        said = llm.chat([{"role": "system", "content": caller_system}] + _caller_view(transcript), temperature=0.9)
        ended = END in said
        said = clean_caller_text(said).replace(END, "").strip()
        if said:
            transcript.append({"role": "caller", "text": said})
        if ended:
            break
        reply = llm.chat([{"role": "system", "content": bot_prompt}] + _agent_view(transcript))
        transcript.append({"role": "agent", "text": reply.strip()})
    return transcript
