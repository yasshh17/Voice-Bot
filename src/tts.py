import os
from pathlib import Path
import aiohttp
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class DeepgramTTS:
    """Text-to-speech using Deepgram Aura API."""

    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.url = "https://api.deepgram.com/v1/speak"
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Reuse a single HTTP session for efficiency."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def synthesize(self, text: str) -> bytes:
        """Convert text to mulaw 8kHz audio bytes for Twilio."""
        params = {
            "model": "aura-asteria-en",
            "encoding": "mulaw",
            "sample_rate": "8000",
            "container": "none",
        }
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.post(
                self.url,
                params=params,
                headers=headers,
                json={"text": text},
                timeout=timeout,
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    error = await resp.text()
                    print(f"TTS Error ({resp.status}): {error}")
                    return b""
        except Exception as e:
            print(f"TTS Exception: {e}")
            return b""

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()