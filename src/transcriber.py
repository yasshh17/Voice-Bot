import os
import json
from datetime import datetime
from pathlib import Path


# Project root directory (one level above src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TranscriptManager:
    """Manages loading and saving call transcripts."""

    ACTIVE_CALLS_FILE = Path(__file__).resolve().parent / "active_calls.json"

    @staticmethod
    def load_active_calls() -> dict:
        """Load active call-scenario mappings from file."""
        try:
            with open(TranscriptManager.ACTIVE_CALLS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def get_scenario_for_call(call_sid: str) -> dict:
        """Get the scenario assigned to a specific call."""
        calls = TranscriptManager.load_active_calls()
        call_data = calls.get(call_sid, {})
        return call_data.get(
            "scenario",
            {
                "name": "unknown",
                "system_prompt": "You are a patient calling to schedule an appointment.",
            },
        )

    @staticmethod
    def save_transcript(call_sid: str, scenario_name: str, log: list):
        """Save conversation transcript as both JSON and readable text."""
        transcript_dir = PROJECT_ROOT / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = transcript_dir / f"{timestamp}_{scenario_name}.json"
        with open(json_path, "w") as f:
            json.dump(
                {
                    "call_sid": call_sid,
                    "scenario": scenario_name,
                    "timestamp": timestamp,
                    "conversation": log,
                },
                f,
                indent=2,
            )

        txt_path = transcript_dir / f"{timestamp}_{scenario_name}.txt"
        with open(txt_path, "w") as f:
            f.write(f"Call Transcript: {scenario_name}\n")
            f.write(f"Call SID: {call_sid}\n")
            f.write(f"Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")

            for entry in log:
                if entry["speaker"] == "agent":
                    f.write(f"AGENT:   {entry['text']}\n\n")
                else:
                    f.write(f"PATIENT: {entry['text']}\n\n")

        print(f"Transcripts saved: {json_path}")
        return str(json_path), str(txt_path)

    @staticmethod
    def generate_summary_report():
        """Generate a summary of all transcripts."""
        transcript_dir = PROJECT_ROOT / "transcripts"
        if not transcript_dir.exists():
            print("No transcripts found.")
            return

        json_files = sorted(transcript_dir.glob("*.json"))

        if not json_files:
            print("No transcripts found.")
            return

        print(f"\n{'=' * 60}")
        print(f"TRANSCRIPT SUMMARY - {len(json_files)} calls")
        print(f"{'=' * 60}\n")

        for filepath in json_files:
            with open(filepath, "r") as f:
                data = json.load(f)

            turns = len(data.get("conversation", []))
            scenario = data.get("scenario", "unknown")
            print(f"  {scenario:30s} | {turns:3d} turns | {filepath.name}")

        print()


if __name__ == "__main__":
    TranscriptManager.generate_summary_report()