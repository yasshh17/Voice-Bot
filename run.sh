#!/bin/bash
set -e

echo "============================================"
echo "  Voice Bot - Pretty Good AI Challenge"
echo "============================================"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Source .env for NGROK_URL check
set -a
source .env
set +a

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt --break-system-packages -q

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ERROR: ngrok is not installed."
    echo "Install: brew install ngrok  (Mac) or visit https://ngrok.com/download"
    exit 1
fi

# Check if ngrok is already running
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "ngrok is already running."
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
https = [t['public_url'] for t in tunnels if t['public_url'].startswith('https')]
print(https[0] if https else '')
" 2>/dev/null)
else
    echo "Starting ngrok tunnel..."
    ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    sleep 3

    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
https = [t['public_url'] for t in tunnels if t['public_url'].startswith('https')]
print(https[0] if https else '')
" 2>/dev/null)
fi

if [ -z "$NGROK_URL" ]; then
    echo "ERROR: Could not get ngrok URL."
    [ -n "$NGROK_PID" ] && kill $NGROK_PID 2>/dev/null
    exit 1
fi

NGROK_DOMAIN=$(echo "$NGROK_URL" | sed 's|https://||')

echo "ngrok URL:    $NGROK_URL"
echo "ngrok Domain: $NGROK_DOMAIN"

# Export for the app
export NGROK_URL=$NGROK_URL
export NGROK_DOMAIN=$NGROK_DOMAIN

# Start the FastAPI server
echo ""
echo "Starting server on port 8000..."
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
cd ..
sleep 2

# Check server health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Server is running!"
else
    echo "ERROR: Server failed to start."
    [ -n "$NGROK_PID" ] && kill $NGROK_PID 2>/dev/null
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "============================================"
echo "  Ready! Open a new terminal and run:"
echo "============================================"
echo ""
echo "  cd src"
echo "  python3 caller.py list            - List scenarios"
echo "  python3 caller.py single 0        - Run one scenario"
echo "  python3 caller.py all             - Run all scenarios"
echo "  python3 caller.py all 45          - Custom delay (seconds)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $SERVER_PID 2>/dev/null
    [ -n "$NGROK_PID" ] && kill $NGROK_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT

wait $SERVER_PID