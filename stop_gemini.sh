#!/bin/bash
# Stop Gemini Wrapper
# Usage: ./stop_gemini.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.gemini_wrapper.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  Pas de PID file trouvé"
    echo "   Recherche de processus Python..."
    
    # Try to find and kill python processes running gemini_api
    PIDS=$(pgrep -f "gemini_api.py" || true)
    if [ -n "$PIDS" ]; then
        echo "🛑 Arrêt des processus: $PIDS"
        kill $PIDS 2>/dev/null || true
        sleep 2
        kill -9 $PIDS 2>/dev/null || true
        echo "✅ Gemini wrapper arrêté"
    else
        echo "❌ Aucun processus trouvé"
    fi
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "🛑 Arrêt du Gemini wrapper (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "   Force kill..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    echo "✅ Gemini wrapper arrêté"
else
    echo "⚠️  Processus $PID non trouvé"
    rm -f "$PID_FILE"
fi

# Clean up any remaining processes
PIDS=$(pgrep -f "gemini_api.py" || true)
if [ -n "$PIDS" ]; then
    echo "🧹 Nettoyage des processus résiduels..."
    kill -9 $PIDS 2>/dev/null || true
fi

echo "✅ Terminé"
