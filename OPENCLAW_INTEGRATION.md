# Gemini OpenClaw Integration

## Architecture

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   You       │────▶│  OpenClaw            │────▶│  Gemini Wrapper │────▶│  gemini.google  │
│  (Telegram) │     │  (model: gemini-free)│     │  (localhost:8080)│     │  (free tier)    │
└─────────────┘     └─────────────────────┘     └─────────────────┘     └─────────────────┘
```

## Setup

### 1. Start the Gemini Wrapper

```bash
cd ~/gemini-openclaw-wrapper
pip install -r requirements.txt
playwright install chromium

# Start the API server
python gemini_api.py
# or
uvicorn gemini_api:app --host 0.0.0.0 --port 8080
```

### 2. Configure OpenClaw

Add to `~/.openclaw/config.json` or equivalent:

```json5
{
  models: {
    providers: {
      "gemini-free": {
        baseUrl: "http://localhost:8080",
        api: "openai-completions",
        apiKey: "not-needed",
        models: [
          {
            id: "gemini-scraper",
            name: "Gemini Free",
            reasoning: false,
            input: ["text"],
            contextWindow: 32000,
            maxTokens: 8192,
          }
        ]
      }
    }
  },
  agents: {
    defaults: {
      model: { primary: "gemini-free/gemini-scraper" }
    }
  }
}
```

### 3. Switch models in OpenClaw

```bash
# Switch to Gemini
openclaw model gemini-free/gemini-scraper

# Switch back to default
openclaw model kimi-coding/k2-6
```

## Features

- **Free** — No API key needed
- **No auth** — Gemini 3 Flash works without Google account
- **OpenAI-compatible** — Uses standard `/v1/chat/completions` endpoint
- **Command parsing** — Extracts executable commands from responses

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Start the wrapper: `python gemini_api.py` |
| "Model not found" | Check config and restart OpenClaw |
| Slow responses | Normal — browser automation takes 5-15s |
