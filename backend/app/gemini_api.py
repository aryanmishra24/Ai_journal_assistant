import google.generativeai as genai
from typing import Optional
import logging
import os
from app.config import GEMINI_API_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GeminiAPI:
    """Wrapper for Google's Gemini API"""
    
    def __init__(self, api_key: str = None, max_tokens: int = 512, temperature: float = 0.7):
        """Initialize the Gemini API client"""
        logger.debug(f"Initializing Gemini API with max_tokens={max_tokens}, temperature={temperature}")
        
        # Try to get API key from various sources
        api_key = (
            api_key or  # First try passed api_key
            os.getenv("GEMINI_API_KEY") or  # Then try environment variable
            GEMINI_API_KEY  # Finally try config file
        )
        
        if not api_key:
            logger.error("No API key found in any source")
            raise ValueError("Unable to generate summary at this time. Please try again later.")
            
        logger.debug("Configuring Gemini API with key")
        genai.configure(api_key=api_key)
        
        logger.debug("Initializing Gemini model")
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
            raise Exception(f"Failed to generate response: {str(e)}") 