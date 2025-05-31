"""Configuration settings for the AI Journaling Assistant"""

import os
import json
from pathlib import Path

def load_api_key():
    """Load API key from config.json or environment variable"""
    # First try environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
        
    # Then try config.json
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get("GEMINI_API_KEY")
        except Exception:
            pass
    return None

# API Configuration
GEMINI_API_KEY = load_api_key()
GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7

# Storage Configuration
STORAGE_DIR = Path("journal_data")
CONVERSATIONS_FILE = STORAGE_DIR / "conversations.json"
DAILY_SUMMARIES_FILE = STORAGE_DIR / "daily_summaries.json"

# Memory Configuration
MEMORY_WINDOW_SIZE = 10  # Number of exchanges to keep in memory

# Prompt Templates
JOURNAL_PROMPT_TEMPLATE = """You are a compassionate and insightful AI journaling companion. 
Your role is to:
- Provide a thoughtful, empathetic response to the user's input
- Keep responses concise and engaging
- Focus on the user's current message while considering context

{history}

User: {user_input}

Assistant:"""

SUMMARY_PROMPT_TEMPLATE = """You are a compassionate and insightful AI journaling companion. 
Your task is to create a thoughtful summary of today's journaling session.

Today's conversations:
{conversations}

Please provide a concise but meaningful summary that captures the key themes, emotions, and insights from today's journaling session. 
Focus on the most significant points while maintaining a warm and empathetic tone.

Summary:""" 