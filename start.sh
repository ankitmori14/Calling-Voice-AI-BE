#!/bin/sh
set -e

# Start LiveKit integration in the background so it runs alongside Uvicorn
echo "Starting LiveKit integration..."
python -m app.core.livekit_integration start &
LIVEKIT_PID=$!

# Start Uvicorn in the foreground (so container stays alive)
echo "Starting Uvicorn..."
exec python -m uvicorn app.main:app
