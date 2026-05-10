#!/bin/bash
# Start Gemini Wrapper + OpenClaw integration
# Usage: ./start_gemini_openclaw.sh [--headless]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="$SCRIPT_DIR"
LOG_DIR="$WRAPPER_DIR/logs"
PID_FILE="$WRAPPER_DIR/.gemini_wrapper.pid"

# Parse args
HEADLESS="true"
if [[ "$1" == "--visible" || "$1" == "-v" ]]; then
    HEADLESS="false"
    echo "🔍 Mode visible activé (pour debug)"
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Gemini wrapper déjà en cours (PID: $PID)"
        echo "   Arrête-le d'abord: ./stop_gemini.sh"
        exit 1
    fi
fi

echo "🚀 Démarrage du Gemini Wrapper..."
echo "   Mode: $([ "$HEADLESS" = "true" ] && echo "headless" || echo "visible")"
echo "   Logs: $LOG_DIR/gemini_wrapper.log"

# Start the wrapper in background
cd "$WRAPPER_DIR"
GEMINI_HEADLESS="$HEADLESS" \
    nohup python gemini_api.py > "$LOG_DIR/gemini_wrapper.log" 2>&1 &

WRAPPER_PID=$!
echo "$WRAPPER_PID" > "$PID_FILE"

echo "✅ Gemini wrapper démarré (PID: $WRAPPER_PID)"
echo ""
echo "📋 Prochaines étapes:"
echo "   1. Attends 5-10s que le browser s'initialise"
echo "   2. Vérifie la santé: curl http://localhost:8080/health"
echo "   3. Configure OpenClaw avec: gemini-free/gemini-scraper"
echo ""
echo "🛑 Pour arrêter: ./stop_gemini.sh"

# Wait a bit and show status
sleep 3
echo ""
echo "🔍 Status:"
curl -s http://localhost:8080/health 2>/dev/null || echo "   ⏳ En cours d'initialisation..."
