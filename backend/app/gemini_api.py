import google.generativeai as genai
from typing import Optional
import logging
from app.config import GEMINI_API_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GeminiAPI:
    """Wrapper for Google's Gemini API"""
    
    def __init__(self, api_key: str = None, max_tokens: int = 512, temperature: float = 0.7):
        """Initialize the Gemini API client"""
        logger.debug(f"Initializing Gemini API with max_tokens={max_tokens}, temperature={temperature}")
        api_key = api_key or GEMINI_API_KEY
        if not api_key:
            raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY in config.py")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.max_tokens = max_tokens
        self.temperature = temperature
        
    def build_prompt(self, template: str, **kwargs) -> str:
        """Build a prompt using the template and provided variables"""
        prompt = template.format(**kwargs)
        logger.debug(f"Built prompt: {prompt[:200]}...")  # Log first 200 chars of prompt
        return prompt
        
    def generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini model"""
        try:
            logger.debug("Generating response from Gemini API...")
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': self.max_tokens,
                    'temperature': self.temperature
                }
            )
            logger.debug(f"Received response: {response.text[:200]}...")  # Log first 200 chars of response
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}" 