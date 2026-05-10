from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_scraper import GeminiScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gemini OpenClaw Wrapper", version="1.0.0")

# Global scraper instance
scraper: Optional[GeminiScraper] = None

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gemini-scraper"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.on_event("startup")
async def startup_event():
    """Initialize the Gemini scraper on startup"""
    global scraper
    logger.info("Starting Gemini OpenClaw Wrapper...")

    try:
        scraper = GeminiScraper()
        await scraper.init_browser()
        await scraper.authenticate()
        logger.info("Gemini scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scraper: {e}")
        logger.warning("Server starting in degraded mode — Gemini unreachable")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scraper
    if scraper:
        await scraper.close()
        logger.info("Gemini scraper closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global scraper
    return {
        "status": "healthy" if scraper and scraper.is_authenticated else "unhealthy",
        "authenticated": scraper.is_authenticated if scraper else False,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    global scraper
    
    if not scraper or not scraper.is_authenticated:
        raise HTTPException(status_code=503, detail="Gemini scraper not initialized")
    
    try:
        # Extract the last user message
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        last_message = user_messages[-1].content
        logger.info(f"Received message: {last_message[:100]}...")
        
        # Send to Gemini and get response
        gemini_response = await scraper.send_message(last_message)
        
        # Parse response for commands
        parsed = scraper.parse_response(gemini_response)
        
        # Format response
        response_content = gemini_response
        if parsed.get("command"):
            response_content = f"{parsed.get('explanation', '')}\n\n```bash\n{parsed['command']}\n```"
        
        # Build OpenAI-compatible response
        response = ChatCompletionResponse(
            id=f"gemini-{datetime.now().timestamp()}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(last_message.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(last_message.split()) + len(response_content.split())
            }
        )
        
        logger.info("Response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gemini-scraper",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "gemini-openclaw-wrapper"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
