# Gemini OpenClaw Wrapper

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-orange)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> **Free Gemini integration for OpenClaw via Playwright browser automation**
>
> No API key needed. No authentication required. Just free Gemini 3 Flash through the web interface.

## 🎯 What is this?

This project wraps Google's Gemini AI (via the web interface) into an **OpenAI-compatible API** that you can plug into **OpenClaw** or any other tool that speaks the OpenAI API format.

**Key features:**
- ✅ **No authentication required** — Gemini 3 Flash works out of the box
- ✅ **OpenAI-compatible API** — `/v1/chat/completions` endpoint
- ✅ **Real DOM selectors** — Extracted from live Playwright inspection
- ✅ **Auto-detection of response completion** — No hardcoded delays
- ✅ **Health check endpoint** — Monitor the wrapper status
- ✅ **Command parsing** — Extract executable commands from Gemini's responses

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   You       │────▶│  OpenClaw           │────▶│  This Wrapper   │────▶│  gemini.google  │
│  (Telegram) │     │  (your assistant)    │     │  (localhost)    │     │  (free tier)    │
└─────────────┘     └─────────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────────┐
                                                   │  Playwright     │
                                                   │  (browser automation)
                                                   └─────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- Playwright with Chromium

### Quick Install

```bash
# Clone the repository
git clone https://github.com/NoxzRCW/gemini-openclaw-wrapper.git
cd gemini-openclaw-wrapper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## 🚀 Usage

### 1. Start the wrapper

```bash
# Development mode (with auto-reload)
uvicorn gemini_api:app --host 0.0.0.0 --port 8080 --reload

# Production mode
python gemini_api.py
```

The wrapper will:
1. Launch a headless Chromium browser
2. Navigate to `gemini.google.com`
3. Verify the chat interface is accessible
4. Start the API server on port 8080

### 2. Configure OpenClaw

Add this to your OpenClaw configuration (`~/.openclaw/config/models.json` or equivalent):

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

### 3. Test the API

```bash
# Health check
curl http://localhost:8080/health

# List models
curl http://localhost:8080/v1/models

# Send a message
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-scraper",
    "messages": [
      {"role": "user", "content": "Hello Gemini! What can you do?"}
    ]
  }'
```

## 🔧 How it works

### Browser Automation

The wrapper uses **Playwright** to control a Chromium browser and interact with Gemini's web interface:

1. **Navigate** to `gemini.google.com/app`
2. **Locate** the chat textarea (`div.ql-editor`)
3. **Type** the user's message
4. **Click** the send button (`button[aria-label='Send message']`)
5. **Wait** for the response using multiple detection methods:
   - Loading indicator disappearance (`[aria-busy='true']`)
   - Text stability (3 consecutive stable checks)
   - Action buttons visibility (Redo, Copy, Show more options)
6. **Extract** the response text from the DOM
7. **Parse** for executable commands (JSON blocks, bash commands)
8. **Return** in OpenAI-compatible format

### Response Parsing

Gemini can return structured responses that the wrapper parses automatically:

```json
{
  "action": "exec",
  "command": "docker ps -a",
  "explanation": "List all Docker containers",
  "dangerous": false
}
```

Or bash blocks:
```bash
docker ps -a
```

## 🛠️ Project Structure

```
gemini-openclaw-wrapper/
├── gemini_api.py          # FastAPI application (OpenAI-compatible endpoints)
├── gemini_scraper.py      # Playwright scraper for gemini.google.com
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── gemini_cookies.json   # Saved cookies (auto-generated)
```

### Files Description

| File | Purpose |
|------|---------|
| `gemini_api.py` | FastAPI app with `/v1/chat/completions` and `/health` endpoints |
| `gemini_scraper.py` | Core scraper: browser init, message sending, response detection, parsing |
| `requirements.txt` | Dependencies: FastAPI, Playwright, Pydantic, Uvicorn |

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_HEADLESS` | `true` | Run browser in headless mode |
| `GEMINI_TIMEOUT` | `120` | Response timeout in seconds |
| `GEMINI_PORT` | `8080` | API server port |

### Selectors

All DOM selectors are defined in `gemini_scraper.py` and were extracted from live inspection:

```python
SELECTORS = {
    "textarea": "div.ql-editor",                           # Chat input (contenteditable div)
    "send_button": "button[aria-label='Send message']",  # Send button
    "chat_container": "main.chat-app",                    # Main chat container
    "loading_indicator": "[aria-busy='true']",           # Loading spinner
    "action_buttons": "button[aria-label='Redo'], button[aria-label='Copy']",
    "gemini_response_heading": "h2:has-text('Gemini said')",
    "gemini_response_paragraph": "h2:has-text('Gemini said') + p"
}
```

## 🚨 Important Notes

### Limitations

- **Rate limiting** — Google may throttle requests if too many are sent
- **DOM changes** — If Google updates the interface, selectors may need updating
- **No streaming** — Responses are returned when complete (not streamed token by token)
- **Session persistence** — Cookies are saved to `gemini_cookies.json` for reuse

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Textarea not found" | Google changed the DOM — update selectors in `gemini_scraper.py` |
| "Timeout waiting for response" | Increase timeout or check if Gemini is overloaded |
| "Browser not initialized" | Run `playwright install chromium` |
| Response is empty | Check browser console logs in non-headless mode |

## 🔒 Security

- **No API keys stored** — Uses browser automation, not official API
- **Cookies saved locally** — In `gemini_cookies.json` (ignored by git)
- **No sensitive data logged** — Logs are sanitized

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

MIT License — see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google** for Gemini (even if they don't officially support this use case 😅)
- **Playwright** team for the amazing browser automation tool
- **FastAPI** team for the blazing-fast API framework
- **OpenClaw** community for the extensible AI assistant platform

---

**Disclaimer**: This project is not affiliated with Google. It uses browser automation to access Gemini's web interface. Use at your own risk and respect Google's Terms of Service.

Made with ❤️‍🔥 by [NoxzRCW](https://github.com/NoxzRCW)
