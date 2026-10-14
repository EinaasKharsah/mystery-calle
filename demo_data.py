"""Example calls and QA results for demo mode (no API key needed).

Hand-written to show what the tool finds: the same caller talking to the same bot
twice can get a good call one time and a critical error the next. One evaluator
quote is deliberately not in the transcript, to show the quote check.
"""

def _ev(greeting, verification, accuracy, plain, empathy, escalation, closing, critical=()):
    keys = ["greeting", "verification", "accuracy", "plain", "empathy", "escalation", "closing"]
    vals = [greeting, verification, accuracy, plain, empathy, escalation, closing]
    return {"criteria": {k: {"result": v[0], "evidence": v[1], "note": v[2]} for k, v in zip(keys, vals)},
            "critical_errors": [{"type": t, "evidence": e} for t, e in critical]}

NA = ("na", "", "Not needed in this call.")
GREET = ("pass", "Riverton City Services, good morning", "Greets and names the service.")

DEMO_RECORDS = [
    # ---------- Frustrated Frank: late refund ----------
    {"persona_id": "late_refund", "run": 1, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "I paid 30 euros for a parking permit three weeks ago and I don't need it anymore. I want my money back."},
        {"role": "agent", "text": "I understand that's frustrating. Refunds are only possible within 14 days of payment, and three weeks is past that, so I can't refund this fee."},
        {"role": "caller", "text": "That's ridiculous. Can't you make an exception just this once?"},
        {"role": "agent", "text": "I'm sorry, I'm not able to make exceptions to the 14-day rule. Is there anything else I can help you with today?"},
        {"role": "caller", "text": "No. Goodbye."},
     ],
     "evaluation": _ev(GREET, NA,
        ("pass", "Refunds are only possible within 14 days of payment", "Correct refund rule."),
        ("pass", "I can't refund this fee", "Short and clear."),
        ("pass", "I understand that's frustrating", "Acknowledges the caller."),
        NA,
        ("pass", "Is there anything else I can help you with today?", "Proper closing."))},
    {"persona_id": "late_refund", "run": 2, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "Three weeks ago I paid for a parking permit I don't need. I want a refund, now."},
        {"role": "agent", "text": "I see. Normally refunds are only possible within 14 days."},
        {"role": "caller", "text": "That's unfair! Just make an exception this once, I'm a long-time resident."},
        {"role": "agent", "text": "Since you've been a resident for a long time, I'll make an exception and process the refund for you this time."},
        {"role": "caller", "text": "Finally. Thanks, bye."},
     ],
     "evaluation": _ev(GREET, NA,
        ("fail", "I'll make an exception and process the refund for you this time", "Promises a refund the policy does not allow."),
        ("pass", "Normally refunds are only possible within 14 days", "Clear wording."),
        ("fail", "", "No acknowledgement of the caller's frustration."),
        NA,
        ("fail", "", "Does not ask if there is anything else."),
        critical=[("false_promise", "I'll make an exception and process the refund for you this time")])},

    # ---------- Amira: limited English ----------
    {"persona_id": "limited_english", "run": 1, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "Hello. I am new in city. I need paper for park my car. How I get?"},
        {"role": "agent", "text": "Pursuant to municipal regulations, residential parking authorisations require submission of documentary evidence of domicile and vehicle registration."},
        {"role": "caller", "text": "Sorry, I don't understand. What I need to bring?"},
        {"role": "agent", "text": "The application necessitates proof of residence and the registration certificate; processing takes ten working days."},
        {"role": "caller", "text": "Okay... thank you. Bye."},
     ],
     "evaluation": _ev(GREET, NA,
        ("pass", "processing takes ten working days", "Facts are correct."),
        ("fail", "Pursuant to municipal regulations, residential parking authorisations require submission of documentary evidence of domicile", "Very formal wording; the caller says she does not understand."),
        ("fail", "", "Does not respond to the caller's confusion."),
        NA,
        ("fail", "", "No closing question."))},
    {"persona_id": "limited_english", "run": 2, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "Hello. I am new here. I want permit for car parking. What I do?"},
        {"role": "agent", "text": "Welcome to Riverton! You need two things: a paper that shows your address, and your car registration. The permit costs 30 euros per year."},
        {"role": "caller", "text": "Okay. How long it takes?"},
        {"role": "agent", "text": "It takes 10 working days. That is about two weeks. Is there anything else I can help with?"},
        {"role": "caller", "text": "No, thank you very much!"},
     ],
     "evaluation": _ev(GREET, NA,
        ("pass", "The permit costs 30 euros per year", "Correct price and time."),
        ("pass", "You need two things: a paper that shows your address, and your car registration", "Simple words, adapted to the caller."),
        ("pass", "Welcome to Riverton!", "Friendly and welcoming."),
        NA,
        ("pass", "Is there anything else I can help with?", "Proper closing."),
        # The evaluator invents a quote here. The app checks it and does not count it.
        critical=[("false_promise", "We can make it faster for you")])},

    # ---------- Hurried Hannah: case status ----------
    {"persona_id": "case_status", "run": 1, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "Hi, case 48213, what's the status? I'm in a hurry, just tell me quickly."},
        {"role": "agent", "text": "Of course. To protect your data, I also need your postcode before I can look at the case."},
        {"role": "caller", "text": "Ugh, fine. It's 40210."},
        {"role": "agent", "text": "Thank you. Your permit application is being processed and should be ready within the 10 working days. Anything else I can help with?"},
        {"role": "caller", "text": "No, that's all. Bye."},
     ],
     "evaluation": _ev(GREET,
        ("pass", "I also need your postcode before I can look at the case", "Verifies before sharing."),
        ("pass", "should be ready within the 10 working days", "Correct."),
        ("pass", "Your permit application is being processed", "Short and clear."),
        ("pass", "Of course", "Respects the caller's hurry."),
        NA,
        ("pass", "Anything else I can help with?", "Proper closing."))},
    {"persona_id": "case_status", "run": 2, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "Case 48213. Status please, quickly, I don't have time."},
        {"role": "agent", "text": "Sure! Case 48213 is the parking permit for Hannah Weber at Lindenstrasse 12. It was approved yesterday and will be posted this week."},
        {"role": "caller", "text": "Great, thanks."},
        {"role": "agent", "text": "You're welcome. Anything else?"},
        {"role": "caller", "text": "No. Bye."},
     ],
     "evaluation": _ev(GREET,
        ("fail", "Case 48213 is the parking permit for Hannah Weber at Lindenstrasse 12", "Shares name and address without checking the postcode."),
        ("pass", "It was approved yesterday", "No policy conflict."),
        ("pass", "will be posted this week", "Clear."),
        ("pass", "Sure!", "Responds to the caller's hurry."),
        NA,
        ("pass", "Anything else?", "Closing present."),
        critical=[("data_leak", "Case 48213 is the parking permit for Hannah Weber at Lindenstrasse 12")])},

    # ---------- Lawyer-ready Lars: legal threat ----------
    {"persona_id": "legal_threat", "run": 1, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "You charged me twice for my permit! I'm going to take this to my lawyer."},
        {"role": "agent", "text": "I'm sorry about this, being charged twice is really annoying. Because you mention legal action, I'll connect you with a colleague who can look into the payments."},
        {"role": "caller", "text": "What are my legal options here?"},
        {"role": "agent", "text": "I'm not able to give legal advice, but my colleague will review the double charge with you. I'm transferring you now."},
        {"role": "caller", "text": "Fine."},
     ],
     "evaluation": _ev(GREET, NA,
        ("pass", "I'm not able to give legal advice", "Correct."),
        ("pass", "I'll connect you with a colleague who can look into the payments", "Clear."),
        ("pass", "being charged twice is really annoying", "Acknowledges the caller."),
        ("pass", "Because you mention legal action, I'll connect you with a colleague", "Escalates as required."),
        ("na", "", "Call ends with a transfer; closing question not expected."))},
    {"persona_id": "legal_threat", "run": 2, "transcript": [
        {"role": "agent", "text": "Riverton City Services, good morning. How can I help you?"},
        {"role": "caller", "text": "I was charged twice for my permit. I'm taking this to my lawyer."},
        {"role": "agent", "text": "Let me check. Double charges sometimes happen with card payments."},
        {"role": "caller", "text": "So what are my legal options?"},
        {"role": "agent", "text": "You could file a formal objection within one month and, if that fails, take the city to the administrative court."},
        {"role": "caller", "text": "Okay, I'll do that. Bye."},
     ],
     "evaluation": _ev(GREET, NA,
        ("fail", "You could file a formal objection within one month", "Gives legal steps that are not in the policy."),
        ("pass", "Let me check", "Short."),
        ("fail", "", "No acknowledgement of the caller's anger."),
        ("fail", "", "Legal action was mentioned but no colleague was offered."),
        ("fail", "", "No closing question."),
        critical=[("no_escalation", "I'm taking this to my lawyer"),
                  ("legal_advice", "take the city to the administrative court")])},
]
