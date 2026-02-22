import os
import sys
import time
import json
from pathlib import Path
from twilio.rest import Client
from dotenv import load_dotenv
from scenarios import SCENARIOS

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

ACTIVE_CALLS_FILE = Path(__file__).resolve().parent / "active_calls.json"


def save_active_call(call_sid: str, scenario: dict):
    """Save call-scenario mapping to file so main.py can read it."""
    try:
        with open(ACTIVE_CALLS_FILE, "r") as f:
            calls = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        calls = {}

    calls[call_sid] = {"scenario": scenario}

    with open(ACTIVE_CALLS_FILE, "w") as f:
        json.dump(calls, f, indent=2)


def make_call(scenario: dict) -> str:
    """Place an outbound call for a given scenario."""
    ngrok_url = os.getenv("NGROK_URL")

    if not ngrok_url:
        print("ERROR: NGROK_URL not set in .env")
        sys.exit(1)

    call = client.calls.create(
        to=os.getenv("TARGET_NUMBER"),
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{ngrok_url}/outbound-handler",
        status_callback=f"{ngrok_url}/call-status",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        timeout=120,
        time_limit=180,
    )

    save_active_call(call.sid, scenario)
    print(f"Call initiated: {call.sid} | Scenario: {scenario['name']}")
    return call.sid


def run_single(scenario_index: int):
    """Run a single scenario by index."""
    if scenario_index < 0 or scenario_index >= len(SCENARIOS):
        print(f"ERROR: Invalid scenario index. Choose 0-{len(SCENARIOS) - 1}")
        list_scenarios()
        sys.exit(1)

    scenario = SCENARIOS[scenario_index]
    print(f"\n{'=' * 60}")
    print(f"Running scenario: {scenario['name']}")
    print(f"{'=' * 60}\n")
    make_call(scenario)


def run_all(delay: int = 60):
    """Run all scenarios sequentially with a delay between calls."""
    print(f"\nRunning all {len(SCENARIOS)} scenarios")
    print(f"Delay between calls: {delay} seconds\n")

    for i, scenario in enumerate(SCENARIOS):
        print(f"\n{'=' * 60}")
        print(f"CALL {i + 1}/{len(SCENARIOS)}: {scenario['name']}")
        print(f"{'=' * 60}")

        make_call(scenario)

        if i < len(SCENARIOS) - 1:
            print(f"\nWaiting {delay} seconds before next call...")
            time.sleep(delay)

    print(f"\n{'=' * 60}")
    print("All calls completed!")
    print("Check the 'transcripts/' folder for results.")
    print(f"{'=' * 60}\n")


def list_scenarios():
    """Print all available scenarios."""
    print("\nAvailable scenarios:")
    print("-" * 40)
    for i, s in enumerate(SCENARIOS):
        print(f"  {i}: {s['name']}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python caller.py list          - List all scenarios")
        print("  python caller.py single <idx>  - Run one scenario")
        print("  python caller.py all            - Run all scenarios")
        print("  python caller.py all <delay>    - Run all with custom delay (seconds)")
        sys.exit(0)

    command = sys.argv[1]

    if command == "list":
        list_scenarios()
    elif command == "single":
        if len(sys.argv) < 3:
            print("ERROR: Provide scenario index.")
            list_scenarios()
            sys.exit(1)
        run_single(int(sys.argv[2]))
    elif command == "all":
        delay = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        run_all(delay)
    else:
        print(f"Unknown command: {command}")
        print("Use: list, single, or all")