import os
import json
import asyncio
from pathlib import Path
import aiohttp
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class RealtimeSTT:
    """Real-time speech-to-text using Deepgram WebSocket via aiohttp."""

    def __init__(self, on_transcript_callback):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.on_transcript = on_transcript_callback
        self.ws = None
        self.session = None
        self._listen_task = None
        self.transcript_buffer = ""

    async def start(self):
        """Connect to Deepgram's streaming STT WebSocket."""
        url = (
            "wss://api.deepgram.com/v1/listen?"
            "model=nova-2&"
            "language=en-US&"
            "encoding=mulaw&"
            "sample_rate=8000&"
            "channels=1&"
            "interim_results=true&"
            "utterance_end_ms=1200&"
            "vad_events=true&"
            "endpointing=300"
        )

        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(
                url, headers=headers, heartbeat=5.0,
            )
            self._listen_task = asyncio.create_task(self._listen())
            print("STT: Connected to Deepgram")
        except Exception as e:
            print(f"STT: Failed to connect: {e}")
            if self.session:
                await self.session.close()

    async def send_audio(self, audio_bytes: bytes):
        """Send audio bytes to Deepgram for transcription."""
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send_bytes(audio_bytes)
            except Exception as e:
                print(f"STT send error: {e}")

    async def _listen(self):
        """Listen for transcription results from Deepgram."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    msg_type = data.get("type", "")

                    if msg_type == "Results":
                        channel = data.get("channel", {})
                        alternatives = channel.get("alternatives", [])

                        if alternatives:
                            transcript = alternatives[0].get("transcript", "").strip()
                            is_final = data.get("is_final", False)

                            if transcript and is_final:
                                self.transcript_buffer += " " + transcript
                                self.transcript_buffer = self.transcript_buffer.strip()

                    elif msg_type == "UtteranceEnd":
                        if self.transcript_buffer:
                            print(f"STT: Utterance: {self.transcript_buffer}")
                            await self.on_transcript(self.transcript_buffer)
                            self.transcript_buffer = ""

                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                    print("STT: WebSocket closed/error")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"STT listen error: {e}")

    async def stop(self):
        """Close the Deepgram connection. Does NOT flush buffer to LLM."""
        # Log any remaining buffer but do NOT trigger LLM call during shutdown
        if self.transcript_buffer:
            print(f"STT: Unflushed buffer on close: {self.transcript_buffer}")
            self.transcript_buffer = ""

        if self._listen_task:
            self._listen_task.cancel()

        if self.ws and not self.ws.closed:
            try:
                await self.ws.send_str(json.dumps({"type": "CloseStream"}))
                await self.ws.close()
            except Exception:
                pass

        if self.session:
            await self.session.close()

        print("STT: Disconnected")