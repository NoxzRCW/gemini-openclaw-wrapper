import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeminiScraper:
    """Scraper for Gemini using Playwright"""
    
    # Real selectors from DOM inspection
    SELECTORS = {
        "textarea": "div.ql-editor",
        "textarea_by_placeholder": "div[contenteditable='true']",
        "send_button": "button[aria-label='Send message']",
        "send_button_by_class": "button.send-button.submit",
        "chat_container": "main.chat-app",
        "chat_container_by_class": ".chat-container",
        "scroll_container": ".chat-history-scroll-container",
        "message_container": ".assistant-messages-primary-container",
        "message_container_open": ".assistant-messages-primary-container.open",
        "primary_message": ".visible-primary-message",
        "loading_indicator": "[aria-busy='true']",
        "action_buttons": "button[aria-label='Redo'], button[aria-label='Copy'], button[aria-label='Show more options']",
        "body_zero_state": "body.zero-state-theme",
        "sign_in_button": ".sign-in-button",
        "gemini_response_heading": "h2:has-text('Gemini said')",
        "gemini_response_paragraph": "h2:has-text('Gemini said') + p"
    }
    
    def __init__(self, headless: bool = True, cookies_file: str = "gemini_cookies.json"):
        self.headless = headless
        self.cookies_file = cookies_file
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_authenticated = False
        self.gemini_url = "https://gemini.google.com/app"
        
    async def init_browser(self):
        """Initialize Playwright browser"""
        logger.info("Initializing browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth args
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
        )
        
        # Create context with viewport
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized")
        
    async def authenticate(self):
        """Check if Gemini is accessible (no auth needed for Gemini Flash)"""
        logger.info("Checking Gemini accessibility...")
        
        # Navigate to Gemini with longer timeout
        try:
            await self.page.goto(self.gemini_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)  # Wait for JS to load
        except Exception as e:
            logger.warning(f"Navigation timeout, retrying... ({e})")
            await self.page.goto(self.gemini_url, wait_until="load", timeout=60000)
            await asyncio.sleep(5)
        
        # Check if the textarea is available (means we can use Gemini)
        textarea = await self.page.query_selector(self.SELECTORS["textarea"])
        if not textarea:
            textarea = await self.page.query_selector(self.SELECTORS["textarea_by_placeholder"])
        
        if textarea:
            self.is_authenticated = True
            logger.info("Gemini is accessible without authentication")
        else:
            logger.warning("Gemini textarea not found - may require auth or page structure changed")
            self.is_authenticated = False
            
        return self.is_authenticated
        
    async def save_cookies(self):
        """Save cookies to file"""
        if self.context:
            cookies = await self.context.cookies()
            with open(self.cookies_file, "w") as f:
                json.dump(cookies, f)
            logger.info(f"Cookies saved to {self.cookies_file}")
            
    async def load_cookies(self):
        """Load cookies from file"""
        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)
            if self.context:
                await self.context.add_cookies(cookies)
            logger.info(f"Cookies loaded from {self.cookies_file}")
            
    async def send_message(self, prompt: str, timeout: int = 120) -> str:
        """Send a message to Gemini and wait for response"""
        if not self.page:
            raise Exception("Browser not initialized")
            
        logger.info(f"Sending message: {prompt[:100]}...")
        
        # Wait for textarea to be available
        textarea = await self.page.wait_for_selector(
            self.SELECTORS["textarea"],
            state="visible",
            timeout=10000
        )
        
        if not textarea:
            # Try alternative selector
            textarea = await self.page.wait_for_selector(
                self.SELECTORS["textarea_by_placeholder"],
                state="visible",
                timeout=10000
            )
        
        if not textarea:
            raise Exception("Textarea not found")
            
        # Clear and type message
        await textarea.click()
        await textarea.fill("")
        await textarea.type(prompt, delay=10)
        
        # Wait for send button to be enabled
        await asyncio.sleep(1)
        
        # Click send button
        send_button = await self.page.query_selector(self.SELECTORS["send_button"])
        if not send_button:
            send_button = await self.page.query_selector(self.SELECTORS["send_button_by_class"])
            
        if not send_button:
            raise Exception("Send button not found")
            
        await send_button.click()
        logger.info("Message sent, waiting for response...")
        
        # Wait for response using multiple methods
        response_text = await self._wait_for_response(timeout)
        
        return response_text
        
    async def _wait_for_response(self, timeout: int = 120) -> str:
        """Wait for Gemini to finish generating response"""
        start_time = asyncio.get_event_loop().time()
        last_text = ""
        stable_count = 0
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Method 1: Check if loading indicator is gone
                loading = await self.page.query_selector(self.SELECTORS["loading_indicator"])
                
                # Method 2: Check if response text is stable
                # Try multiple selectors for the response container
                current_text = await self.page.evaluate("""
                    () => {
                        // Try different selectors for the response
                        const selectors = [
                            '.assistant-messages-primary-container.open',
                            '.assistant-messages-primary-container',
                            '[class*="response"]:last-child',
                            'main.chat-app > div:last-child'
                        ];
                        
                        for (const selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el && el.textContent.length > 50) {
                                return el.textContent;
                            }
                        }
                        
                        // Fallback: look for "Gemini said" heading
                        const headings = document.querySelectorAll('h2');
                        for (const h of headings) {
                            if (h.textContent.includes('Gemini said')) {
                                const nextP = h.nextElementSibling;
                                if (nextP && nextP.tagName === 'P') {
                                    return nextP.textContent;
                                }
                            }
                        }
                        
                        return '';
                    }
                """)
                
                if current_text == last_text and len(current_text) > 0 and not loading:
                    stable_count += 1
                    if stable_count >= 3:  # Text stable for 3 checks
                        logger.info("Response complete (text stable)")
                        return current_text
                else:
                    stable_count = 0
                    last_text = current_text
                    
                # Method 3: Check for action buttons (Redo, Copy, Show more options)
                action_buttons = await self.page.query_selector(self.SELECTORS["action_buttons"])
                if action_buttons and not loading:
                    logger.info("Response complete (action buttons visible)")
                    return current_text
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error during wait: {e}")
                await asyncio.sleep(1)
                
        logger.warning("Timeout waiting for response")
        return last_text
        
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for commands"""
        result = {
            "raw_response": response,
            "command": None,
            "explanation": None,
            "action": None,
            "dangerous": False
        }
        
        # Try to find JSON in response
        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[\s\S]*?"action"[\s\S]*?\}'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if "action" in data:
                        result.update(data)
                        return result
                except:
                    continue
                    
        # Try to find bash commands
        bash_pattern = r'```bash\s*(.*?)\s*```'
        bash_matches = re.findall(bash_pattern, response, re.DOTALL)
        if bash_matches:
            result["command"] = bash_matches[-1].strip()
            result["action"] = "exec"
            
        return result
        
    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")

# For testing
async def main():
    scraper = GeminiScraper(headless=False)
    await scraper.init_browser()
    await scraper.authenticate()
    
    # Test message
    response = await scraper.send_message("Hello Gemini! What can you do?")
    print(f"Response: {response}")
    
    parsed = scraper.parse_response(response)
    print(f"Parsed: {json.dumps(parsed, indent=2)}")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
