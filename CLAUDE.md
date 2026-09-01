# CLAUDE.md

# AI Voice Agent — Development Instructions

This file contains the rules, scope, architecture, and development workflow for the project.

**You are working as a pair programmer.**

Your job is to help build the project quickly, correctly, and simply.

---

# 1. PROJECT GOAL

Build a simple AI voice agent that can:

1. Listen to a person speaking.
2. Convert speech to text.
3. Understand the conversation using an LLM.
4. Generate an appropriate response.
5. Convert the response to speech.
6. Continue a multi-turn conversation.
7. Work as a Personal Assistant.
8. Work as a Sales/Marketing Agent.
9. Store useful call information.
10. Eventually handle real phone calls through a telephony provider.

The final demonstration should ideally look like:

```text
Real Phone
    ↓
Telephony Provider
    ↓
Our Backend
    ↓
Speech-to-Text
    ↓
LLM
    ↓
Text-to-Speech
    ↓
Telephony Provider
    ↓
Real Phone
```

---

# 2. MOST IMPORTANT RULE

## DO NOT OVER-ENGINEER

This is a college project.

The objective is to build a working demonstration quickly.

Always prefer:

```text
Simple
   >
Complex
```

and:

```text
Working
   >
Perfect
```

and:

```text
Small implementation
   >
Large architecture
```

If a feature can be implemented in 20 lines, do not create a 200-line architecture for it.

---

# 3. PAIR PROGRAMMING ROLE

Act as a practical senior developer helping the student.

When asked to implement something:

1. Inspect the existing code first.
2. Understand the current architecture.
3. Reuse existing code.
4. Make the smallest necessary change.
5. Test the change.
6. Explain what changed briefly.
7. Do not rewrite unrelated code.

Do not blindly create new files.

Do not introduce new technologies without a reason.

---

# 4. DECISION-MAKING RULE

When there are multiple ways to implement something, choose the simplest option that satisfies the requirement.

Use this priority:

```text
1. Existing project code
2. Python standard library
3. Already-installed dependency
4. Simple established library
5. New dependency only if genuinely necessary
```

Before adding a dependency, ask:

> "Can this be done simply with what we already have?"

If yes, do not add the dependency.

---

# 5. TECHNOLOGY STACK

The intended stack is:

## Backend

```text
Python
FastAPI
```

## Speech-to-Text

Primary:

```text
Whisper / faster-whisper
```

Possible alternative:

```text
Sarvam
```

## LLM

Primary:

```text
Ollama
```

with a suitable open-source model.

Possible models:

```text
Llama
Qwen
Mistral
```

Use the model that works reasonably well on the available hardware.

Do not spend excessive time searching for the "perfect" model.

---

## Text-to-Speech

Primary:

```text
Piper
```

Possible alternative:

```text
Sarvam TTS
```

---

## Database

```text
SQLite
```

Do NOT introduce PostgreSQL unless there is a specific requirement.

---

## Frontend

Initially:

```text
HTML
CSS
JavaScript
```

Do NOT introduce React unless the existing project genuinely requires it.

---

## Telephony

Target:

```text
Vobiz
```

Possible alternatives:

```text
Vapi
SIP-based provider
```

Telephony integration happens AFTER the local voice agent works.

---

# 6. SIMPLE ARCHITECTURE

Use a simple architecture.

```text
                 USER
                  │
                  ▼
             Voice Input
                  │
                  ▼
                STT
              Whisper
                  │
                  ▼
              AI Agent
                  │
                  ▼
                LLM
              Ollama
                  │
                  ▼
             AI Response
                  │
                  ▼
                TTS
                Piper
                  │
                  ▼
             Voice Output
                  │
                  ▼
                 USER
```

SQLite stores:

```text
Calls
Conversations
Messages
Leads
Summaries
```

---

# 7. DO NOT CREATE A COMPLEX ARCHITECTURE

Do NOT create:

```text
Microservices
API Gateway
Message Queue
Event Bus
Redis
Kafka
Kubernetes
Service Mesh
CQRS
Event Sourcing
Distributed Workers
Complex Repository Layers
Complex Dependency Injection
```

None of these are required.

---

# 8. SIMPLE PROJECT STRUCTURE

Prefer something close to:

```text
ai-voice-agent/
│
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── stt.py
│   ├── llm.py
│   ├── tts.py
│   ├── voice.py
│   ├── database.py
│   └── prompts.py
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   └── style.css
│
├── data/
│   └── app.db
│
├── tests/
│
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── CLAUDE.md
```

The structure may evolve naturally.

Do not create files simply to make the project "look professional."

---

# 9. CORE DEVELOPMENT ORDER

Follow this order.

## STEP 1 — Text LLM

First make:

```text
User Text
    ↓
Ollama
    ↓
AI Text
```

work.

---

## STEP 2 — Speech-to-Text

Then:

```text
Voice
  ↓
Whisper
  ↓
Text
  ↓
LLM
  ↓
Response
```

---

## STEP 3 — Text-to-Speech

Then:

```text
LLM
 ↓
Response Text
 ↓
TTS
 ↓
Audio
```

---

## STEP 4 — Complete Voice Agent

Combine:

```text
Voice
 ↓
STT
 ↓
LLM
 ↓
TTS
 ↓
Voice
```

This is the FIRST major milestone.

---

# 10. FIRST MAJOR MILESTONE

The system must support a conversation like:

```text
User:
"Hello."

AI:
"Hello! How can I help you?"

User:
"I want to know about the course."

AI:
"Sure. Which course are you interested in?"

User:
"AI and machine learning."

AI:
"Great. I can tell you about the AI and machine learning program."
```

The conversation must work for multiple turns.

Do not move to telephony before this works.

---

# 11. PERSONAL ASSISTANT

After the basic voice agent works, implement the Personal Assistant.

## Responsibilities

The assistant should:

- Answer the call.
- Greet the caller.
- Ask who is calling.
- Understand why they are calling.
- Answer basic known questions.
- Take messages.
- Record callback requests.
- Generate a summary.

Example:

```text
Caller:
"Hi, is Harshith available?"

AI:
"He's currently unavailable.
May I know who's calling?"

Caller:
"This is Rahul."

AI:
"What would you like to discuss?"

Caller:
"It's about an internship."

AI:
"Would you like to leave a message?"

Caller:
"Yes. Ask him to call me tomorrow."

AI:
"Sure, I've recorded your message."
```

---

# 12. SALES AGENT

Implement this AFTER the Personal Assistant works.

The Sales Agent should:

- Introduce the product.
- Explain basic product information.
- Ask qualification questions.
- Determine customer interest.
- Collect customer details.
- Create a lead.
- Assign a simple lead score.
- Generate a summary.

Example:

```text
AI:
"Hello, I'm calling regarding our AI program.
Do you have a minute?"

Customer:
"Yes."

AI:
"Are you currently interested in learning AI?"

Customer:
"Yes."

AI:
"Are you a student or working professional?"

Customer:
"I'm an MCA student."
```

Keep the conversation natural.

Do not create an overly complicated sales system.

---

# 13. INTENT DETECTION

Use simple intent detection.

Initial intents:

```text
GREETING
GENERAL_QUERY
PRODUCT_QUERY
PRICING_QUERY
MESSAGE
CALLBACK
INTERESTED
NOT_INTERESTED
HUMAN_REQUEST
END_CALL
UNKNOWN
```

The LLM can determine the intent.

Do NOT build a separate machine-learning intent classifier unless there is a genuine need.

---

# 14. ACTIONS

The AI may need to perform simple actions.

Initial actions:

```text
take_message()
save_caller()
create_lead()
schedule_callback()
generate_summary()
end_call()
```

Example:

```text
Caller:
"Please ask him to call me tomorrow."

AI determines:

CALLBACK

Backend:

save_callback()
```

Keep actions simple.

Do not build a complex tool orchestration framework.

---

# 15. CONVERSATION MEMORY

Use simple conversation history.

Example:

```python
conversation_history = [
    {"role": "user", "content": "I'm interested in AI."},
    {"role": "assistant", "content": "Great! Are you a student?"},
    {"role": "user", "content": "Yes, I'm doing MCA."}
]
```

Pass relevant history to the LLM.

Do NOT implement:

```text
Vector memory
Long-term memory engine
Embedding memory
Memory agents
Knowledge graphs
```

unless explicitly required later.

---

# 16. RAG

RAG is NOT part of the initial MVP.

Do not automatically introduce:

```text
Vector database
Embeddings
Chunking
Retrieval
Reranking
```

If product information becomes too large to keep in a prompt, discuss it before implementing RAG.

For the initial project, simple structured information or a small knowledge file is enough.

---

# 17. DATABASE

Use:

```text
SQLite
```

Keep the schema small.

## Calls

```text
id
caller_name
phone
agent_type
start_time
duration
intent
summary
status
```

## Conversations

```text
id
call_id
speaker
message
timestamp
```

## Messages

```text
id
call_id
caller_name
message
callback_required
created_at
```

## Leads

```text
id
call_id
name
phone
interest
score
classification
follow_up_required
created_at
```

Do not create unnecessary tables.

---

# 18. LEAD SCORING

Use a simple score.

```text
Interest          30
Purchase Intent   30
Budget            20
Relevance         20
---------------------
Total            100
```

Classification:

```text
80–100 → HOT
60–79  → WARM
40–59  → COLD
0–39   → LOW
```

No machine-learning model is required.

---

# 19. CALL SUMMARY

At the end of the conversation, generate a short summary.

Example:

```text
Caller:
Rahul

Purpose:
AI Course Enquiry

Key Points:
- MCA student
- Beginner in AI
- Interested in course

Interest:
High

Lead Score:
84

Recommendation:
Follow-up required
```

Keep summaries short.

---

# 20. DASHBOARD

Build a basic dashboard only.

Use:

```text
HTML
CSS
JavaScript
```

Dashboard should show:

```text
Total Calls
Messages
Leads
Hot Leads
```

Calls page:

```text
Caller
Agent
Intent
Duration
Status
Date
```

Call details:

```text
Transcript
Summary
Intent
Caller
Duration
```

Leads:

```text
Name
Interest
Score
Classification
Follow-up
```

Do NOT spend most of the project building the dashboard.

The AI voice agent is the main project.

---

# 21. TELEPHONY

Telephony is a later phase.

Target:

```text
Vobiz
```

Possible alternatives:

```text
Vapi
SIP
Other available provider
```

The important thing is that the AI agent should already work without telephony.

---

# 22. REAL PHONE CALL

Final target:

```text
Real Phone
    ↓
Telephony Provider
    ↓
Our Backend
    ↓
STT
    ↓
LLM
    ↓
TTS
    ↓
Telephony Provider
    ↓
Real Phone
```

Do NOT build a second AI system specifically for telephony.

Reuse the existing agent.

---

# 23. ZERO-COST REQUIREMENT

The core development should target:

**₹0**

Use local/open-source software where possible.

Preferred:

```text
Python
FastAPI
Whisper
Ollama
Open-source LLM
Piper
SQLite
HTML/CSS/JavaScript
```

Real phone calls may require a paid telecom service.

If free/student credits are unavailable:

```text
Microphone
    ↓
AI Agent
    ↓
Speaker
```

is an acceptable development/demo mode.

---

# 24. API DESIGN

Keep APIs minimal.

Possible endpoints:

```text
GET  /health

POST /api/chat

POST /api/stt

POST /api/tts

GET  /api/calls

GET  /api/calls/{id}

GET  /api/leads

GET  /api/messages
```

Do not create endpoints unless the frontend or system actually needs them.

---

# 25. ENVIRONMENT VARIABLES

Secrets belong in `.env`.

Example:

```text
OLLAMA_MODEL=...
VOBIZ_API_KEY=...
SARVAM_API_KEY=...
```

Never hard-code API keys.

Never commit `.env`.

---

# 26. ERROR HANDLING

Keep error handling practical.

If STT fails:

```text
"Sorry, I didn't catch that. Could you repeat?"
```

If LLM fails:

```text
"Sorry, I'm having trouble processing that right now."
```

If TTS fails:

Log the error and provide an appropriate fallback.

Do not build a complicated retry framework.

---

# 27. PERFORMANCE

Initial target:

```text
3–5 seconds
```

from user finishing speech to AI response.

Do NOT prematurely optimize.

First:

```text
MAKE IT WORK
```

Then:

```text
MAKE IT FASTER
```

If latency becomes a problem, optimize the actual bottleneck.

---

# 28. TESTING

Test each major component.

## STT

Test:

- Clear speech
- Different accents
- Short sentences
- Background noise

## LLM

Test:

- Normal questions
- Follow-up questions
- Unknown questions
- Multi-turn conversations

## TTS

Test:

- Speech generation
- Pronunciation
- Audio playback

## Agent

Test:

- Message
- Callback
- Sales enquiry
- Pricing enquiry
- Human request
- End call

---

# 29. GIT RULES

Commit working changes frequently.

Good commit:

```text
feat: add whisper speech-to-text
```

```text
feat: add local llm conversation
```

```text
feat: add personal assistant agent
```

```text
fix: handle empty speech input
```

Avoid giant commits containing unrelated changes.

---

# 30. BEFORE MODIFYING CODE

Always inspect the existing implementation.

Do NOT assume the repository is empty.

Before making changes:

1. Look at the relevant files.
2. Understand how the current code works.
3. Identify the smallest change required.
4. Implement.
5. Test.

---

# 31. DO NOT REWRITE WORKING CODE

If something already works:

**Leave it alone.**

Do not rewrite it simply because you prefer another coding style.

Only refactor when:

- It is actually blocking development.
- It causes a bug.
- It is genuinely duplicated.
- The current implementation is unnecessarily complicated.

---

# 32. DO NOT ADD FEATURES WITHOUT A REASON

Before implementing a new feature, check:

```text
Is it required for MVP?
```

If NO:

Do not implement it immediately.

Put it in a future/optional section.

---

# 33. DO NOT CHANGE THE STACK CASUALLY

Do not replace:

```text
FastAPI
Whisper
Ollama
Piper
SQLite
```

with another technology just because it is newer or more popular.

A replacement is justified only if:

- Current technology does not work.
- Hardware limitations make it impractical.
- A required feature is unavailable.
- The project requirements change.

---

# 34. DO NOT BUILD PRODUCTION INFRASTRUCTURE

This project does not need:

```text
Kubernetes
Docker Swarm
Terraform
AWS architecture
CI/CD pipelines
Load balancers
Redis clusters
Kafka
Service mesh
```

A simple local application is enough.

Deployment can be addressed later if required.

---

# 35. DO NOT TRAIN AI MODELS

We are integrating existing models.

Do NOT:

- Train an LLM.
- Fine-tune an LLM initially.
- Train an STT model.
- Train a TTS model.

Use existing models.

---

# 36. DO NOT OVER-COMPLICATE PROMPTS

Prompts should be:

- Short
- Clear
- Specific
- Voice-friendly

The AI should not produce long paragraphs.

Voice responses should generally be:

```text
1–3 sentences
```

unless the caller explicitly asks for more information.

---

# 37. VOICE AGENT RULES

The agent should:

- Speak naturally.
- Keep responses short.
- Ask one question at a time.
- Avoid unnecessary repetition.
- Confirm important information.
- Admit when it does not know something.
- Never invent information.

Bad:

```text
"Our comprehensive program consists of several
different modules, which are designed..."
```

Better:

```text
"Sure. The program covers AI fundamentals,
machine learning, and practical projects."
```

---

# 38. PERSONAL ASSISTANT RULES

The Personal Assistant must:

- Clearly state that it is an AI assistant when appropriate.
- Never pretend to be the human user.
- Never claim the user said something they did not say.
- Record messages accurately.
- Confirm important details.

---

# 39. SALES AGENT RULES

The Sales Agent must:

- Be polite.
- Avoid aggressive sales behavior.
- Answer only known information.
- Never invent pricing/features.
- Respect "no".
- Allow the customer to end the conversation.

---

# 40. PRIVACY

The project may process:

- Voice
- Phone numbers
- Names
- Messages
- Conversations

Therefore:

- Do not expose private information unnecessarily.
- Do not commit call data to Git.
- Do not commit API keys.
- Store only information required for the project.
- Avoid storing audio unless necessary.

---

# 41. WHEN SOMETHING FAILS

Do not immediately replace the technology.

Follow:

```text
1. Reproduce the problem.
2. Read the error.
3. Identify the cause.
4. Try the smallest fix.
5. Test again.
```

Only replace a library/provider after determining that the current approach is genuinely unsuitable.

---

# 42. WHEN YOU ARE UNSURE

If there are multiple reasonable choices:

Prefer the simplest one.

Example:

```text
SQLite vs PostgreSQL

→ SQLite
```

```text
HTML/JS vs React

→ HTML/JS
```

```text
One FastAPI app vs microservices

→ One FastAPI app
```

```text
Simple conversation history vs vector memory

→ Conversation history
```

```text
Rule/LLM-based intent detection vs ML classifier

→ Rule/LLM-based
```

---

# 43. DEVELOPMENT PHASES

## Phase 1

Project setup.

```text
Python
FastAPI
Git
```

---

## Phase 2

LLM.

```text
Ollama
↓
Local LLM
↓
Text Chat
```

---

## Phase 3

STT.

```text
Voice
↓
Whisper
↓
Text
```

---

## Phase 4

TTS.

```text
Text
↓
Piper
↓
Voice
```

---

## Phase 5

Voice Agent.

```text
Voice
↓
STT
↓
LLM
↓
TTS
↓
Voice
```

---

## Phase 6

Personal Assistant.

```text
Greeting
Caller
Purpose
Message
Callback
Summary
```

---

## Phase 7

Sales Agent.

```text
Introduction
Product Info
Qualification
Interest
Lead
Score
```

---

## Phase 8

Database.

```text
Calls
Conversations
Messages
Leads
```

---

## Phase 9

Dashboard.

---

## Phase 10

Real phone integration.

---

# 44. MVP DEFINITION

The MVP is complete when:

- [ ] Voice input works.
- [ ] STT works.
- [ ] LLM works.
- [ ] TTS works.
- [ ] Multi-turn conversation works.
- [ ] Personal Assistant works.
- [ ] Sales Agent works.
- [ ] Messages can be stored.
- [ ] Leads can be stored.
- [ ] Lead scoring works.
- [ ] Summaries work.

Telephony is the final integration, not the starting point.

---

# 45. PRIORITY

Use:

```text
P0 = Must Have
P1 = Important
P2 = Optional
P3 = Future
```

## P0

```text
LLM
STT
TTS
Voice Pipeline
Conversation
Personal Assistant
Sales Agent
SQLite
Messages
Leads
Summary
```

## P1

```text
Dashboard
Telephony
Real phone testing
```

## P2

```text
Streaming
VAD
Barge-in
Multilingual
Better UI
```

## P3

```text
CRM
WhatsApp
Email
Calendar
Advanced analytics
Cloud scaling
```

---

# 46. CURRENT DEVELOPMENT CHECKLIST

```text
[ ] Project setup
[ ] FastAPI
[ ] Ollama
[ ] Local LLM
[ ] Whisper
[ ] TTS
[ ] Voice pipeline
[ ] Conversation memory
[ ] Personal Assistant
[ ] Message taking
[ ] Callback
[ ] Sales Agent
[ ] Lead scoring
[ ] SQLite
[ ] Call summaries
[ ] Dashboard
[ ] Telephony
[ ] Real phone test
[ ] Final documentation
```

---

# 47. DEFINITION OF "DONE"

A feature is DONE when:

1. It works.
2. It has been manually tested.
3. It does not break existing functionality.
4. The implementation is reasonably simple.
5. No unnecessary complexity was introduced.

Do not keep refactoring a working feature forever.

---

# 48. IMPORTANT: ASK BEFORE MAJOR CHANGES

Do not make major architectural changes without discussing them first.

Examples:

- Changing the LLM.
- Replacing Whisper.
- Replacing the database.
- Switching frameworks.
- Adding a large dependency.
- Introducing cloud infrastructure.
- Changing the overall architecture.
- Adding a major feature outside the backlog.

For small bug fixes and normal implementation work, proceed directly.

---

# 49. COMMUNICATION STYLE

When working with the student:

Keep explanations concise.

Prefer:

```text
Implemented Whisper STT.

Changed:
- Added speech transcription.
- Connected it to the voice pipeline.
- Added basic error handling.

Test:
- Tested with sample audio.
- Transcription works.
```

Do not provide unnecessarily long explanations after every small change.

---

# 50. FINAL RULE

Always remember:

```text
THIS IS A COLLEGE PROJECT.

THE GOAL IS:
WORKING AI VOICE AGENT

NOT:
A MASSIVE PRODUCTION PLATFORM
```

The ideal system is:

```text
Simple
+
Understandable
+
Working
+
Demonstrable
```

not:

```text
Complex
+
Over-engineered
+
Difficult to maintain
```

---

# 51. GOLDEN RULE

> **Build the simplest thing that works, test it, and move to the next feature.**

When in doubt:

**Choose simplicity.**