from datetime import datetime, date
from typing import Dict, List, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
from sqlalchemy.orm import Session
import logging

from app.config import (
    MEMORY_WINDOW_SIZE,
    JOURNAL_PROMPT_TEMPLATE,
    SUMMARY_PROMPT_TEMPLATE,
    GEMINI_API_KEY,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE
)
from app.gemini_api import GeminiAPI
from app.models.journal import JournalEntry, DailySummary
from app.models.mood import Mood

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIJournalingAssistant:
    """Main AI Journaling Assistant class"""
    
    def __init__(self, api_key: str = None, max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = DEFAULT_TEMPERATURE):
        """Initialize the AI Journaling Assistant"""
        self.api = GeminiAPI(api_key or GEMINI_API_KEY, max_tokens, temperature)
        
        # Initialize memory with a window of last N exchanges
        self.memory = ConversationBufferWindowMemory(
            k=MEMORY_WINDOW_SIZE,
            return_messages=True
        )
        
    def chat(self, user_input: str, db: Session) -> str:
        """Process user input and return AI response"""
        try:
            # Build conversation history
            history = self.memory.chat_memory.messages
            history_text = ""
            
            if history:
                history_text = "\nPrevious conversation:\n"
                for msg in history[-6:]:
                    if isinstance(msg, HumanMessage):
                        history_text += f"Journal Entry: {msg.content}\n"
                    elif isinstance(msg, AIMessage):
                        history_text += f"AI Response: {msg.content}\n"
            
            # Build and send prompt
            prompt = self.api.build_prompt(
                JOURNAL_PROMPT_TEMPLATE,
                history=history_text,
                user_input=user_input
            )
            
            response_text = self.api.generate_response(prompt)
            
            # Update memory
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response_text)
            
            return response_text
            
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return f"I apologize, but I encountered an error while processing your journal entry. Please try again."
            
    def _generate_daily_summary(self, db: Session, entries: List[JournalEntry] = None) -> str:
        """Generate a summary of today's journaling session"""
        try:
            # Get today's entries from database if not provided
            if entries is None:
                today = date.today()
                entries = db.query(JournalEntry).filter(
                    JournalEntry.created_at >= datetime.combine(today, datetime.min.time()),
                    JournalEntry.created_at <= datetime.combine(today, datetime.max.time())
                ).all()
            
            if not entries:
                return "📝 No journal entries found for today to summarize."
            
            # Format entries for summary with timestamps
            conversation_text = "\n".join([
                f"Entry {i+1} ({entry.created_at.strftime('%H:%M')}):\n{entry.content}\n"
                for i, entry in enumerate(entries)
            ])
            
            # Debug: Print the entries being formatted
            print("DEBUG - Entries being formatted:")
            print(conversation_text)
            print("DEBUG - End of entries")
            
            # Build and send summary prompt
            prompt = self.api.build_prompt(
                SUMMARY_PROMPT_TEMPLATE,
                conversations=conversation_text
            )
            
            # Debug: Print the prompt being sent
            print("DEBUG - Prompt being sent to Gemini:")
            print(prompt)
            print("DEBUG - End of prompt")
            
            summary = self.api.generate_response(prompt)
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {e}"

    def generate_mood_summary(self, moods: List[Mood]) -> str:
        """Generate a summary of today's moods"""
        try:
            if not moods:
                return "No mood entries found for today to summarize."

            # Format mood entries for summary
            mood_text = "\n".join([
                f"Mood Entry ({mood.created_at.strftime('%H:%M')}):\n"
                f"Score: {mood.mood_score}/10\n"
                f"Label: {mood.mood_label}\n"
                f"Notes: {mood.notes if mood.notes else 'No notes'}\n"
                for mood in moods
            ])

            # Build prompt for mood summary
            prompt = f"""Please analyze the following mood entries and provide a concise summary of the user's emotional state throughout the day:

{mood_text}

Please provide a brief summary that captures:
1. The overall emotional trend
2. Any notable patterns or changes
3. A gentle, supportive reflection on their mood journey

Keep the summary concise, empathetic, and focused on emotional well-being."""

            # Generate summary using AI
            try:
                logger.debug("Generating mood summary with Gemini API...")
                summary = self.api.generate_response(prompt)
                logger.debug(f"Generated summary: {summary[:200]}...")
                return summary
            except Exception as e:
                logger.error(f"Error from Gemini API: {str(e)}")
                raise Exception(f"Failed to generate mood summary: {str(e)}")

        except Exception as e:
            logger.error(f"Error generating mood summary: {str(e)}")
            raise Exception(f"Failed to generate mood summary: {str(e)}") 