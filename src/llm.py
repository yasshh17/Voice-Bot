import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class ConversationEngine:
    """Manages LLM-powered patient conversation with scenario-specific personas."""

    def __init__(self, scenario: dict):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.scenario = scenario
        self.messages = [
            {
                "role": "system",
                "content": (
                    f"You are a patient calling a doctor's office. "
                    f"{scenario['system_prompt']}\n\n"
                    f"RULES:\n"
                    f"- Respond naturally and conversationally, like a real phone call\n"
                    f"- Keep responses SHORT - 1-2 sentences max, as people do on the phone\n"
                    f"- Never say you're an AI or a bot\n"
                    f"- React naturally to what the agent says\n"
                    f"- If the agent says something wrong or confusing, push back gently\n"
                    f"- Say 'goodbye' and end the call naturally when your task is complete\n"
                    f"- Do NOT use any special characters, emojis, or markdown\n"
                    f"- Speak like a normal person on the phone"
                ),
            }
        ]
        self.transcript = []

    async def get_opening_line(self) -> str:
        """Generate the first thing the patient says when the call connects."""
        self.messages.append(
            {
                "role": "user",
                "content": (
                    "The phone is ringing and someone just picked up. "
                    "Say your opening line as the patient calling in. "
                    "Keep it natural and short, like 'Hi, I'm calling to...'"
                ),
            }
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                max_tokens=150,
                temperature=0.8,
                timeout=10,
            )

            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            self.transcript.append({"speaker": "patient_bot", "text": reply})
            return reply
        except Exception as e:
            print(f"LLM error on opening: {e}")
            fallback = "Hi, I'm calling to schedule an appointment."
            self.messages.append({"role": "assistant", "content": fallback})
            self.transcript.append({"speaker": "patient_bot", "text": fallback})
            return fallback

    async def respond(self, agent_text: str) -> str:
        """Generate a response to what the agent said."""
        self.transcript.append({"speaker": "agent", "text": agent_text})

        self.messages.append(
            {"role": "user", "content": f"[The receptionist/agent says]: {agent_text}"}
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                max_tokens=150,
                temperature=0.8,
                timeout=10,
            )

            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            self.transcript.append({"speaker": "patient_bot", "text": reply})
            return reply
        except Exception as e:
            print(f"LLM error: {e}")
            fallback = "I'm sorry, could you repeat that?"
            self.messages.append({"role": "assistant", "content": fallback})
            self.transcript.append({"speaker": "patient_bot", "text": fallback})
            return fallback

    def get_transcript(self) -> list:
        return self.transcript

    def is_call_complete(self) -> bool:
        """Check if the patient has said goodbye."""
        if not self.transcript:
            return False
        last_entry = self.transcript[-1]
        if last_entry["speaker"] == "patient_bot":
            goodbye_phrases = [
                "goodbye", "bye", "thank you, bye",
                "thanks, bye", "have a good",
            ]
            return any(
                phrase in last_entry["text"].lower() for phrase in goodbye_phrases
            )
        return False