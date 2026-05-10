# Gemini OpenClaw Wrapper

Wrapper OpenClaw pour Gemini via Playwright (gratuit, sans API).

## Architecture

```
Toi → OpenClaw → Gemini API Wrapper (localhost:8080) → Playwright → gemini.google.com
```

## Installation

```bash
cd gemini-openclaw-wrapper
pip install -r requirements.txt
playwright install chromium
```

## Configuration

### 1. Configurer OpenClaw

Ajouter dans `~/.openclaw/config/models.json` (ou équivalent) :

```json
{
  "gemini-free": {
    "provider": "openai-compatible",
    "baseUrl": "http://localhost:8080/v1",
    "model": "gemini-scraper",
    "apiKey": "not-needed"
  }
}
```

### 2. Lancer le wrapper

```bash
# Mode interactif (pour la première connexion)
python gemini_api.py

# Ou avec uvicorn directement
uvicorn gemini_api:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Première connexion

La première fois, le wrapper ouvrira Chrome en mode visible.
Connecte-toi manuellement à Google, puis le wrapper sauvegardera les cookies.

### 4. Utilisation

```bash
# Tester l'API
curl http://localhost:8080/health

# Envoyer un message
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-scraper",
    "messages": [{"role": "user", "content": "Hello Gemini!"}]
  }'
```

## Fichiers

- `gemini_api.py` — API FastAPI compatible OpenAI
- `gemini_scraper.py` — Scraper Playwright pour Gemini
- `requirements.txt` — Dépendances

## Notes

- **Mode headless** : Après la première auth, tu peux passer `headless=True`
- **Cookies** : Sauvegardés dans `gemini_cookies.json`
- **Fragilité** : Si Google change le DOM, le scraper peut casser
- **Rate limiting** : Ne pas spammer, Google détecte les bots

## Dépannage

**"Not authenticated"**
→ Supprime `gemini_cookies.json` et relance en mode visible

**"Timeout waiting for response"**
→ Augmente le timeout dans `gemini_scraper.py`

**"Send button not found"**
→ Google a changé le DOM, met à jour les sélecteurs
