#!/bin/bash
# Quick status check for Gemini Wrapper

echo "🔍 Gemini Wrapper Status"
echo "======================"
echo ""

# Check if running
PID_FILE="$(dirname "$0")/.gemini_wrapper.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ En cours d'exécution (PID: $PID)"
    else
        echo "❌ Processus mort (PID: $PID)"
    fi
else
    echo "❌ Pas démarré"
fi

echo ""
echo "🌐 API Status:"
curl -s http://localhost:8080/health 2>/dev/null || echo "   ❌ Non accessible"

echo ""
echo "📊 Logs récents:"
LOG_FILE="$(dirname "$0")/logs/gemini_wrapper.log"
if [ -f "$LOG_FILE" ]; then
    tail -n 5 "$LOG_FILE"
else
    echo "   Pas de logs"
fi

echo ""
echo "🔧 Actions:"
echo "   Démarrer:  ./start_gemini.sh"
echo "   Arrêter:   ./stop_gemini.sh"
echo "   Logs:      tail -f logs/gemini_wrapper.log"
