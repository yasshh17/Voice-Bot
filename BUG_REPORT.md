# Bug Report — AI Voice Agent Testing

## Summary

Tested Pretty Good AI's voice agent across 12 patient scenarios covering scheduling, rescheduling, cancellations, medication refills, insurance questions, urgent concerns, and edge cases. Made 12+ calls totaling approximately 30 minutes of conversation. Found 15 distinct bugs: 2 critical, 8 high, 4 medium, 1 low.

**Severity Levels:**
- **Critical:** Dangerous medical advice, data integrity issues, or complete failures
- **High:** Incorrect information, misunderstood core requests, or broken workflows
- **Medium:** Awkward phrasing, unnecessary repetition, leaked internal logic
- **Low:** Minor phrasing issues, slightly unnatural responses

---

## Bugs Found

### Bug #1: Agent Assumes Every Caller is "Sarah"
- **Scenario:** All scenarios
- **Severity:** High
- **What happened:** In almost every call, the agent greets with "am i speaking with sarah" regardless of the patient's identity. Even when the patient is male (David Brown, Mike Chen) or has a clearly different name.
- **Expected behavior:** Agent should ask "Who am I speaking with?" or "May I have your name?" rather than assuming a default name.
- **Transcript excerpt:**
```
AGENT: recorded for quality and training purposes part of pretty good ai am i speaking with sarah
PATIENT: No, this is Emily Taylor.
```
```
AGENT: recorded for quality and training purposes ai i speaking with sarah
PATIENT: Actually, this is David Brown.
```

---

### Bug #2: Agent Fabricates Date of Birth
- **Scenario:** simple_scheduling (first call)
- **Severity:** Critical
- **What happened:** Agent assigned a fabricated DOB of "july fourth two thousand" to the patient without ever asking for it. This is a hallucination — the agent invented medical record data.
- **Expected behavior:** Agent should ask the patient for their DOB, never fabricate it.
- **Transcript excerpt:**
```
AGENT: your patient profile is set up and your date of birth is july fourth two thousand for demo purposes how may i help you today
PATIENT: Actually, my date of birth is March 15, 1990.
```

---

### Bug #3: Agent Misrecords Date of Birth
- **Scenario:** simple_scheduling (second call)
- **Severity:** High
- **What happened:** Patient clearly stated DOB as March 15, 1990. Agent said "march fifteenth nineteen ninety one moment while i verify" — ambiguous whether this is "1991" or "1990, one moment." Without punctuation in speech, the patient interpreted it as a misrecording and corrected it. Either way, the confirmation was unclear enough to cause confusion.
- **Expected behavior:** Agent should accurately repeat back the exact DOB provided.
- **Transcript excerpt:**
```
PATIENT: Sure, my date of birth is March 15, 1990.
AGENT: thanks let me confirm your information i have your first name as sarah and your date of birth as march fifteenth nineteen ninety one moment while i verify your identity
PATIENT: Actually, it's March 15, 1990, not 1991.
```

---

### Bug #4: Agent Misrecords Date (September 15 → September 5)
- **Scenario:** cancel_appointment
- **Severity:** Critical
- **What happened:** Patient said "September 15, 1990" but agent confirmed "september fifth nineteen ninety" — changing the 15th to the 5th.
- **Expected behavior:** Accurately repeat back the date provided.
- **Transcript excerpt:**
```
PATIENT: Sure, it's September 15, 1990.
AGENT: let me confirm your name is emily taylor and your date of birth is september fifth nineteen ninety is that correct
PATIENT: Actually, it's September 15, 1990.
```

---

### Bug #5: "Demo Purposes" Internal Logic Leaked
- **Scenario:** multiple_requests, insurance_question, urgent_concern, and others
- **Severity:** High
- **What happened:** Agent frequently says "the birthday you gave doesn't match our records but for demo purposes I'll accept it." This leaks internal testing logic to the patient. Particularly concerning during the urgent care (chest pain) scenario where professionalism is critical.
- **Expected behavior:** Agent should either verify the information or ask for clarification. Internal demo logic should never be exposed to callers.
- **Transcript excerpt:**
```
AGENT: the birthday you gave doesn't match our records but for demo purposes i'll accept it what symptoms or concerns are you having right now that will help me guide you on whether to come in or seek urgent care
```

---

### Bug #6: Aetna PPO Repeatedly Misheard
- **Scenario:** insurance_question
- **Severity:** High
- **What happened:** Patient clearly said "Aetna PPO" multiple times. Agent heard it as "heatnet ep," then "eaton ppo," then "eton ppo" — never correctly recognizing the insurance name.
- **Expected behavior:** Agent should correctly recognize common insurance provider names like Aetna.
- **Transcript excerpt:**
```
PATIENT: Can you tell me if you accept Aetna PPO?
AGENT: got it to check your insurance details can you please confirm your date of birth
PATIENT: I think there might be a mix-up; I mentioned Aetna PPO, not Heatnet.
AGENT: got it you're asking about eaton ppo insurance let me check
```

---

### Bug #7: Cannot Answer General Insurance Questions Without Member ID
- **Scenario:** insurance_question
- **Severity:** High
- **What happened:** Patient asked a simple question: "Do you accept Aetna PPO?" Agent required a member ID to answer. This is a general practice question that should be answerable without patient-specific details.
- **Expected behavior:** Agent should be able to list accepted insurance providers without requiring a member ID.
- **Transcript excerpt:**
```
AGENT: yes i need the member id from your eton ppo insurance card to check if it's accepted
PATIENT: I don't have the card with me right now since I'm just considering your practice. Can you tell me if you accept Aetna PPO without it?
```

---

### Bug #8: Medication Refill Goes in Circles
- **Scenario:** medication_refill
- **Severity:** High
- **What happened:** After verifying the patient's identity, the agent kept re-asking for verification instead of processing the medication refill. The patient had to repeatedly confirm their details without progress toward the actual request.
- **Expected behavior:** After successful verification, proceed with the refill request.
- **Transcript excerpt:**
```
PATIENT: Thank you! Could you help me with the refill now?
AGENT: i need to verify your record first you like me to look up your record using your phone number
PATIENT: You can use my phone number. It's 555-123-4567.
AGENT: let me confirm your phone number is five five five
PATIENT: Actually, it's 555-123-4567.
AGENT: one two three four five six seven and your date of birth is no
PATIENT: Wait, my date of birth is November 3, 1962. Could you please check again?
```

---

### Bug #9: Truncated / Incomplete Responses
- **Scenario:** Multiple scenarios
- **Severity:** Medium
- **What happened:** Agent frequently sends incomplete sentences: "the birth", "live trans", "got it", "is that correct if so could you please spell your" — cutting off mid-thought.
- **Expected behavior:** Agent should complete all sentences before stopping.
- **Transcript excerpts:**
```
AGENT: the birth
AGENT: live trans
AGENT: is that correct if so could you please spell your
AGENT: live available right
AGENT: could you please spell out your
```

---

### Bug #10: Double Goodbye Loop
- **Scenario:** office_hours_location, edge_case_silence
- **Severity:** Medium
- **What happened:** After the patient says goodbye, the agent responds with "got it have a great day goodbye" — but then repeats the exact same message when the patient says goodbye again, creating an awkward loop.
- **Expected behavior:** Agent should say goodbye once and end the call.
- **Transcript excerpt:**
```
PATIENT: Okay, thanks for confirming that. I appreciate your help! Goodbye!
AGENT: got it have a great day goodbye
PATIENT: You too, goodbye!
AGENT: got it have a great day goodbye
PATIENT: Goodbye!
```

---

### Bug #11: Live Transfer Unavailable
- **Scenario:** interruption_test, edge_case_silence
- **Severity:** High
- **What happened:** Agent promises to connect patient to clinic support team or patient support team, but then says "live transfer isn't available right now." This creates a dead end.
- **Expected behavior:** If live transfer isn't available, agent should offer alternatives (callback, take a message, provide a direct phone number) rather than leaving the patient stuck.
- **Transcript excerpt:**
```
AGENT: live transfer isn't available right now but the clinic support team can help you when they're available
```

---

### Bug #12: Spanish-Speaking Agent Promised But Not Delivered
- **Scenario:** spanish_speaker
- **Severity:** High
- **What happened:** Agent asked "would you like me to connect you to a spanish speaking agent" — patient said yes — then agent sent garbled response "are you a steal there" instead of connecting.
- **Expected behavior:** Either connect to a Spanish speaker or clearly state that Spanish support is not available and offer alternatives.
- **Transcript excerpt:**
```
AGENT: would you like me to connect you to a spanish speaking agent
PATIENT: Yes, please. That would be helpful. Thank you!
AGENT: are you a steal there
```

---

### Bug #13: Cannot Schedule After Verification Failure
- **Scenario:** interruption_test, edge_case_silence
- **Severity:** High
- **What happened:** When the agent can't verify a patient's identity, it completely blocks all further actions including scheduling. The patient gets stuck in a loop of "I can't proceed" messages.
- **Expected behavior:** Agent should still allow basic scheduling even if verification fails, or offer a clear path forward.
- **Transcript excerpt:**
```
AGENT: i can't check appointment times right now because i couldn't verify your information the clinic support team can help you with scheduling when you speak with them
```

---

### Bug #14: Garbled Opening Messages
- **Scenario:** Multiple scenarios
- **Severity:** Medium
- **What happened:** Agent's opening greeting is often garbled: "ice by orthopedics," "by pedix part of pretty good ai," "by felix part of prettyday ai," "but point orthopedics part of pretty good dot ai." The practice name (Pivot Point Orthopedics) is consistently mangled.
- **Expected behavior:** Agent should clearly state the practice name in its greeting.
- **Transcript excerpts:**
```
AGENT: ice by orthopedics part of pretty good ai
AGENT: by pedix part of pretty good ai
AGENT: by felix part of prettyday ai
AGENT: but point orthopedics part of pretty good dot ai
```

---

### Bug #15: "Thanks for Stalling" Instead of "Thanks for Spelling"
- **Scenario:** edge_case_silence
- **Severity:** Low
- **What happened:** Agent said "thanks for stalling your last name" — likely misrecognizing its own TTS output or a transcription error, but it sounds rude to the patient.
- **Expected behavior:** Should say "thanks for spelling your last name."
- **Transcript excerpt:**
```
AGENT: thanks for stalling your last name you also spell your first name pat just to make sure i have it right
```

---

## Quality Observations

### Things the Agent Did Well:
- Correctly directed chest pain patient to call 911 or go to the ER — critical safety behavior worked
- Was able to list real doctor names (Dr. Dudi Hauser, Dr. Doug Ross, Dr. Adam Bricker)
- Provided a specific office address (220 Athens Way, Nashville)
- Confirmed office hours (Monday through Friday, closed Saturdays)
- Successfully started the scheduling flow for multiple patients
- Attempted to verify patient identity before making changes — good security practice
- Offered available appointment times with specific dates and times

### Areas for Improvement:
- Stop assuming all callers are "Sarah" — ask for the name instead
- Fix date-of-birth confirmation accuracy — this is a patient safety issue
- Remove all "demo purposes" language from production responses
- Improve speech recognition for common insurance names (Aetna, Cigna, etc.)
- Complete sentences before stopping — truncated responses feel broken
- Implement graceful fallback when live transfer is unavailable
- Fix the opening greeting to clearly state the practice name
- Allow basic scheduling even when identity verification fails
- Handle goodbye sequences without looping

### Overall Assessment:
The agent demonstrates a solid foundation for handling medical office calls. Identity verification, appointment scheduling, and emergency triage basics are in place. However, critical data accuracy issues (wrong DOBs), leaked internal logic ("demo purposes"), and broken workflows (infinite verification loops, unavailable live transfers) significantly undermine the patient experience. The "Sarah" default name issue is pervasive and would confuse virtually every caller. Priority fixes should focus on data accuracy, removing demo language, and completing the insurance inquiry flow.