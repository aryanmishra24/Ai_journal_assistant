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
from app.utils.timezone import to_ist

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
            # Get recent entries from database for context
            recent_entries = db.query(JournalEntry).order_by(
                JournalEntry.created_at.desc()
            ).limit(6).all()
            
            # Build conversation history from database entries
            history_text = ""
            if recent_entries:
                history_text = "\nPrevious conversation:\n"
                for entry in reversed(recent_entries):  # Reverse to get chronological order
                    history_text += f"Journal Entry: {entry.content}\n"
                    if entry.ai_response:
                        history_text += f"AI Response: {entry.ai_response}\n"
            
            # Build and send prompt
            prompt = self.api.build_prompt(
                JOURNAL_PROMPT_TEMPLATE,
                history=history_text,
                user_input=user_input
            )
            
            response_text = self.api.generate_response(prompt)
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"I apologize, but I encountered an error while processing your journal entry. Please try again."
            
    def _generate_daily_summary(self, db: Session, entries: List[JournalEntry] = None) -> str:
        """Generate a summary of today's journaling session"""
        try:
            if not entries:
                return "📝 No journal entries found to summarize."
            
            # Get the date of the first entry
            entry_date = entries[0].created_at.date()
            is_today = entry_date == datetime.now().date()
            tense = "today" if is_today else "on " + entry_date.strftime("%B %d, %Y")
            entries_text = "Today's conversations" if is_today else f"Conversations from {entry_date.strftime('%B %d, %Y')}"
            
            # Format entries for summary with IST timestamps
            conversation_text = "\n".join([
                f"Entry {i+1} ({to_ist(entry.created_at).strftime('%H:%M')}):\n{entry.content}\n"
                for i, entry in enumerate(entries)
            ])
            
            # Debug: Print the entries being formatted
            logger.debug("DEBUG - Entries being formatted:")
            logger.debug(conversation_text)
            logger.debug("DEBUG - End of entries")
            
            # Build and send summary prompt
            prompt = f"""You are a compassionate and insightful AI journaling companion. 
Your task is to create a thoughtful summary of the journaling session for {tense}.

{entries_text}:
{conversation_text}

Please provide a concise but meaningful summary that captures the key themes, emotions, and insights from these journal entries. 
Focus on the most significant points while maintaining a warm and empathetic tone.
Summary:"""
            
            # Debug: Print the prompt being sent
            logger.debug("DEBUG - Prompt being sent to Gemini:")
            logger.debug(prompt)
            logger.debug("DEBUG - End of prompt")
            
            summary = self.api.generate_response(prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {e}"

    def generate_mood_summary(self, moods: List[Mood]) -> str:
        """Generate a summary of mood entries using AI."""
        try:
            # Get the date of the first mood entry
            entry_date = moods[0].created_at.date()
            is_today = entry_date == datetime.now().date()
            tense = "today" if is_today else "on " + entry_date.strftime("%B %d, %Y")
            entries_text = "Today's mood entries" if is_today else f"Mood entries for {entry_date.strftime('%B %d, %Y')}"
            
            # Format the mood entries
            formatted_entries = []
            for mood in moods:
                entry_time = mood.created_at.strftime("%H:%M")
                formatted_entries.append(f"Entry ({entry_time}):\n{mood.mood_label} - {mood.mood_score}/10\n{mood.notes or ''}")
            
            # Create the prompt
            prompt = f"""You are a compassionate and insightful AI journaling companion. 
Your task is to create a thoughtful summary of the mood entries for {tense}.

{entries_text}:
{chr(10).join(formatted_entries)}

Please provide a concise but meaningful summary that captures the key themes, emotions, and insights from these mood entries. 
Focus on the most significant points while maintaining a warm and empathetic tone.
Summary:"""
            
            logger.debug("DEBUG - Prompt being sent to Gemini:")
            logger.debug(prompt)
            logger.debug("DEBUG - End of prompt")
            
            # Generate the summary using Gemini
            response = self.api.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating mood summary: {str(e)}")
            return "Unable to generate mood summary at this time."

    def generate_journal_summary(self, entries: List[JournalEntry]) -> str:
        """Generate a summary of journal entries using AI."""
        try:
            # Get the date of the first entry
            entry_date = entries[0].created_at.date()
            is_today = entry_date == datetime.now().date()
            tense = "today" if is_today else "on " + entry_date.strftime("%B %d, %Y")
            entries_text = "Today's conversations" if is_today else f"Conversations from {entry_date.strftime('%B %d, %Y')}"
            
            # Format the entries
            formatted_entries = []
            for entry in entries:
                entry_time = entry.created_at.strftime("%H:%M")
                formatted_entries.append(f"Entry {entry.id} ({entry_time}):\n{entry.content}")
            
            # Create the prompt
            prompt = f"""You are a compassionate and insightful AI journaling companion. 
Your task is to create a thoughtful summary of the journaling session for {tense}.

{entries_text}:
{chr(10).join(formatted_entries)}

Please provide a concise but meaningful summary that captures the key themes, emotions, and insights from these journal entries. 
Focus on the most significant points while maintaining a warm and empathetic tone.
Summary:"""
            
            logger.debug("DEBUG - Prompt being sent to Gemini:")
            logger.debug(prompt)
            logger.debug("DEBUG - End of prompt")
            
            # Generate the summary using Gemini
            response = self.api.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating journal summary: {str(e)}")
            return "Unable to generate journal summary at this time." 