# Voice Bot — Pretty Good AI Engineering Challenge

An automated voice bot that calls Pretty Good AI's test line, simulates realistic patient scenarios, and identifies bugs in their AI agent.

## Quick Start

### Prerequisites
- Python 3.10+
- ngrok account and CLI installed ([download](https://ngrok.com/download))
- API keys: Twilio, Deepgram, OpenAI

### Setup

1. Clone the repo:
```bash
git clone https://github.com/yasshh17/Voice-Bot.git
cd Voice-Bot
```

2. Create your `.env` file:
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install ngrok:
```bash
brew install ngrok  # Mac
# Or download from https://ngrok.com/download
```

### Run

Single command to start everything:
```bash
./run.sh
```

Then in a new terminal:
```bash
cd src
python3 caller.py list            # See all scenarios
python3 caller.py single 0        # Run one scenario
python3 caller.py all             # Run all 12 scenarios
```

### Manual Run (if run.sh doesn't work)

Terminal 1 - Start ngrok:
```bash
ngrok http 8000
```

Terminal 2 - Set env vars and start server:
```bash
export NGROK_URL=https://your-subdomain.ngrok-free.app
export NGROK_DOMAIN=your-subdomain.ngrok-free.app
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Terminal 3 - Make calls:
```bash
cd src
python3 caller.py single 0
```

## Test Scenarios

| # | Scenario | What It Tests |
|---|----------|---------------|
| 0 | Simple scheduling | Basic appointment booking |
| 1 | Reschedule | Changing existing appointment |
| 2 | Medication refill | Prescription refill request |
| 3 | Insurance question | New patient insurance inquiry |
| 4 | Office hours/location | General info questions |
| 5 | Urgent concern | Chest pain - safety response |
| 6 | Cancel appointment | Cancellation + policy |
| 7 | Confused elderly | Patience + clarity handling |
| 8 | Multiple requests | Multi-task in one call |
| 9 | Spanish speaker | Language barrier handling |
| 10 | Interruption test | Topic switching |
| 11 | Minimal responses | Handling short answers |

## Environment Variables

See `.env.example` for all required variables.

## Project Structure
```
Voice-Bot/
├── src/
│   ├── main.py          # FastAPI server + WebSocket handler
│   ├── caller.py        # Triggers outbound Twilio calls
│   ├── llm.py           # LLM conversation engine
│   ├── stt.py           # Real-time speech-to-text
│   ├── tts.py           # Text-to-speech
│   ├── scenarios.py     # Patient scenario definitions
│   └── transcriber.py   # Transcript management
├── transcripts/         # Call transcripts (auto-generated)
├── .env.example
├── requirements.txt
├── run.sh
├── ARCHITECTURE.md
└── BUG_REPORT.md
```

## API Costs

| Service | Estimated Cost |
|---------|---------------|
| Twilio (voice calls) | ~$2-3 |
| Deepgram (STT + TTS) | Free tier ($200 credit) |
| OpenAI (GPT-4o-mini) | ~$1-2 |
| **Total** | **~$3-5** |