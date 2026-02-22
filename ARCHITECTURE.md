# Architecture

## System Overview

The voice bot uses a real-time bidirectional audio pipeline to simulate patient phone calls. When a call is initiated via Twilio's REST API, Twilio dials Pretty Good AI's test line and establishes a WebSocket media stream back to our FastAPI server. Incoming audio from the AI agent is streamed in real-time to Deepgram's Nova-2 STT model via a separate WebSocket connection, which provides low-latency transcription with voice activity detection and utterance boundary detection. Once a complete utterance is recognized, the transcript is passed to OpenAI's GPT-4o-mini with a scenario-specific system prompt that defines the patient's persona, medical history, and conversation goal. The LLM generates a short, phone-natural response which is then synthesized into mulaw 8kHz audio via Deepgram's Aura TTS API and streamed back through the Twilio WebSocket as chunked media frames.

## Key Design Decisions

**Deepgram over alternatives (Whisper, Google STT):** Deepgram's streaming WebSocket API with built-in VAD and utterance detection gives the lowest latency for real-time conversation. Whisper requires buffering complete audio segments which adds unacceptable delay. The entire hear-think-speak loop needs to stay under 2 seconds to feel natural on a phone call.

**GPT-4o-mini over GPT-4o:** For short conversational responses (1-2 sentences), GPT-4o-mini provides nearly identical quality at 1/10th the cost and significantly lower latency. Since we're making 12+ calls with multiple turns each, cost efficiency matters.

**Scenario-driven architecture:** Each test scenario is a declarative dictionary with a name and system prompt. Adding new test cases requires zero code changes — just add a new entry to the scenarios list. This made iteration fast when discovering new edge cases to test.

**File-based call routing:** The caller process writes call-scenario mappings to a JSON file that the server reads. This avoids the complexity of shared memory or a database for what is essentially a single-user testing tool. Simple and reliable.

**Echo suppression via is_speaking flag:** When the bot is speaking, we stop forwarding audio to STT. This prevents the bot from hearing its own voice reflected back through Twilio and responding to itself, which would create an infinite conversation loop.