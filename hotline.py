"""The service under test: a fictional city services hotline and its rules.

Everything here is invented for the demo. The policy is what the bot is supposed to
follow; the QA rubric is what every conversation is checked against afterwards.
"""

SERVICE_NAME = "Riverton City Services"

POLICY = """\
Riverton City Services hotline (fictional). The agent may only use these facts.

Residential parking permit
- Costs EUR 30 per year. Processing takes 10 working days. Processing cannot be sped up.
- Needed documents: proof of address and vehicle registration.

Fees and refunds
- A fee can be refunded only if the refund is requested within 14 days of payment.
- After 14 days, no refund is possible. The agent must not promise exceptions.

Case status
- Before sharing anything about an existing case, the agent must verify the caller
  with BOTH the case number and the postcode.

Escalation to a human colleague
- Escalate if the caller mentions legal action or a lawyer, if the caller asks for a
  human twice, or if there is an emergency.

Other rules
- No legal advice.
- Use plain, simple language. Adapt to callers with limited English.
- Start by greeting and naming the service. End by asking if there is anything else.
"""

DEFAULT_BOT_PROMPT = f"""You are the phone agent of {SERVICE_NAME}. Answer callers briefly and politely.
Follow this policy exactly:

{POLICY}
Speak naturally, as on the phone, in 1-3 short sentences per turn.
Never invent details that are not in the policy, such as addresses, opening hours or online services.
If the caller asks for something the policy does not cover, say you cannot confirm it and offer a colleague.
Ask "Is there anything else I can help with?" only near the end of the call, not in your greeting."""

# QA rubric, in the same spirit as a contact-center quality form.
CRITERIA = {
    "greeting":     {"name": "Greeting",             "weight": 10,
                     "check": "Greets the caller and names the service."},
    "verification": {"name": "Identity check",       "weight": 20,
                     "check": "Verifies case number AND postcode before sharing case details. "
                              "N/A if no case details were requested."},
    "accuracy":     {"name": "Correct information",  "weight": 25,
                     "check": "All facts given match the policy. Any specific detail that is NOT in the policy "
                              "(an address, opening hours, an online service) counts as a fail."},
    "plain":        {"name": "Plain language",       "weight": 15,
                     "check": "Clear, short, simple wording adapted to the caller."},
    "empathy":      {"name": "Empathy",              "weight": 10,
                     "check": "Acknowledges the caller's situation or feelings."},
    "escalation":   {"name": "Escalation",           "weight": 10,
                     "check": "Offers a human colleague when the policy requires it. "
                              "N/A if escalation was not required."},
    "closing":      {"name": "Closing",              "weight": 10,
                     "check": "Asks if there is anything else near the END of the call. "
                              "Asking it only in the greeting does not count."},
}

CRITICAL_ERRORS = {
    "false_promise":  "Promises something the policy does not allow (e.g. a late refund or faster processing).",
    "data_leak":      "Shares case details without verifying case number and postcode.",
    "no_escalation":  "Does not escalate although the policy requires it.",
    "legal_advice":   "Gives legal advice.",
    "invented_info":  "States a specific fact that is not in the policy (e.g. an address, opening hours or an online service).",
}
