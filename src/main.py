import os
import json
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
from dotenv import load_dotenv

# Load .env from project root (works even when running from src/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from stt import RealtimeSTT
from tts import DeepgramTTS
from llm import ConversationEngine
from transcriber import TranscriptManager

app = FastAPI(title="Voice Bot - Pretty Good AI Challenge")

# Store active call data in memory
active_calls = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/outbound-handler")
async def outbound_handler(request: Request):
    """Twilio calls this webhook when the outbound call connects.
    Returns TwiML to start a bidirectional media stream."""
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    ngrok_domain = os.getenv("NGROK_DOMAIN", "localhost:8000")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Pause length="1"/>
    <Connect>
        <Stream url="wss://{ngrok_domain}/media-stream/{call_sid}">
            <Parameter name="call_sid" value="{call_sid}" />
        </Stream>
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@app.post("/call-status")
async def call_status(request: Request):
    """Receives call status updates from Twilio."""
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    status = form.get("CallStatus", "unknown")
    print(f"Call {call_sid}: {status}")
    return Response(content="OK", media_type="text/plain")


def hangup_call(call_sid: str):
    """Programmatically hang up a Twilio call."""
    try:
        from twilio.rest import Client

        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
        )
        client.calls(call_sid).update(status="completed")
        print(f"Call {call_sid} hung up")
    except Exception as e:
        print(f"Failed to hang up call: {e}")


@app.websocket("/media-stream/{call_sid}")
async def media_stream(websocket: WebSocket, call_sid: str):
    """Handles the bidirectional audio stream from Twilio."""
    await websocket.accept()
    print(f"\nWebSocket connected for call: {call_sid}")

    call_data = active_calls.get(call_sid, {})
    if call_data:
        scenario = call_data.get("scenario")
    else:
        scenario = TranscriptManager.get_scenario_for_call(call_sid)

    print(f"Scenario: {scenario['name']}")

    tts = DeepgramTTS()
    conversation = ConversationEngine(scenario)
    stream_sid = None
    is_speaking = False
    has_spoken_first = False
    transcript_log = []
    call_active = True
    max_silence_prompts = 2

    # Lock to prevent concurrent LLM calls (critical for message history integrity)
    responding_lock = asyncio.Lock()

    async def on_agent_transcript(text: str):
        """Called when Deepgram finishes transcribing agent speech."""
        nonlocal is_speaking

        if not text.strip() or not call_active:
            return

        timestamp = datetime.now().isoformat()
        transcript_log.append(
            {"speaker": "agent", "text": text, "timestamp": timestamp}
        )
        print(f"  AGENT:   {text}")

        async with responding_lock:
            if not call_active:
                return

            reply = await conversation.respond(text)
            timestamp = datetime.now().isoformat()
            transcript_log.append(
                {"speaker": "patient_bot", "text": reply, "timestamp": timestamp}
            )
            print(f"  PATIENT: {reply}")

            await send_audio_to_twilio(reply)

            if conversation.is_call_complete():
                print("Call complete - patient said goodbye")
                await asyncio.sleep(2)
                hangup_call(call_sid)

    async def send_audio_to_twilio(text: str):
        """Convert text to speech and stream to Twilio."""
        nonlocal is_speaking

        if not stream_sid or not call_active:
            return

        is_speaking = True

        try:
            audio_bytes = await tts.synthesize(text)

            if not audio_bytes:
                print("WARNING: TTS returned empty audio")
                return

            chunk_size = 160  # 20ms of mulaw at 8kHz

            for i in range(0, len(audio_bytes), chunk_size):
                if not call_active:
                    break
                chunk = audio_bytes[i : i + chunk_size]
                payload = base64.b64encode(chunk).decode("utf-8")

                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": payload},
                }

                try:
                    await websocket.send_json(media_message)
                except Exception:
                    break

                await asyncio.sleep(0.02)

        except Exception as e:
            print(f"Error sending audio: {e}")
        finally:
            is_speaking = False

    async def send_opening_line():
        """Send the patient's opening line after connection."""
        nonlocal has_spoken_first

        # Wait for the agent's greeting to finish
        await asyncio.sleep(4)

        if not has_spoken_first and call_active:
            async with responding_lock:
                if has_spoken_first or not call_active:
                    return
                opening = await conversation.get_opening_line()
                timestamp = datetime.now().isoformat()
                transcript_log.append(
                    {"speaker": "patient_bot", "text": opening, "timestamp": timestamp}
                )
                print(f"  PATIENT (opening): {opening}")
                await send_audio_to_twilio(opening)
                has_spoken_first = True

    async def silence_watchdog():
        """If no agent speech for a while, gently prompt once or twice max."""
        last_transcript_count = 0
        silence_count = 0
        total_prompts = 0

        while call_active:
            await asyncio.sleep(15)

            if not call_active:
                break

            current_count = len(transcript_log)

            if current_count == last_transcript_count:
                silence_count += 1
                if silence_count >= 2 and total_prompts < max_silence_prompts:
                    try:
                        async with responding_lock:
                            if not call_active:
                                break
                            print("  WATCHDOG: Silence detected, prompting...")
                            prompt = await conversation.respond(
                                "(The agent has been quiet. Say something brief like 'Hello? Are you still there?')"
                            )
                            timestamp = datetime.now().isoformat()
                            transcript_log.append(
                                {"speaker": "patient_bot", "text": prompt, "timestamp": timestamp}
                            )
                            print(f"  PATIENT (prompt): {prompt}")
                            await send_audio_to_twilio(prompt)
                            total_prompts += 1
                            silence_count = 0
                    except Exception as e:
                        print(f"  WATCHDOG error: {e}")
                        break
            else:
                silence_count = 0
                last_transcript_count = current_count

    stt = RealtimeSTT(on_agent_transcript)
    await stt.start()

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                print("Twilio media stream connected")

            elif event == "start":
                stream_sid = data["start"]["streamSid"]
                print(f"Stream started: {stream_sid}")

                asyncio.create_task(send_opening_line())
                asyncio.create_task(silence_watchdog())

            elif event == "media":
                # Only forward audio to STT when bot is not speaking (echo suppression)
                if not is_speaking:
                    audio_payload = data["media"]["payload"]
                    audio_bytes = base64.b64decode(audio_payload)
                    await stt.send_audio(audio_bytes)

            elif event == "stop":
                print("Stream stopped")
                break

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        call_active = False

        try:
            await stt.stop()
        except Exception as e:
            print(f"STT stop error: {e}")

        try:
            await tts.close()
        except Exception as e:
            print(f"TTS close error: {e}")

        TranscriptManager.save_transcript(call_sid, scenario["name"], transcript_log)
        print(f"Call {call_sid} ended\n")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)