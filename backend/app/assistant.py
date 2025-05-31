from app.config import MEMORY_WINDOW_SIZE, JOURNAL_PROMPT_TEMPLATE, SUMMARY_PROMPT_TEMPLATE
from app.database import get_db
from app.models.journal import JournalEntry, DailySummary
from app.gemini_api import GeminiAPI
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIJournalingAssistant:
    def __init__(self):
        self.gemini_api = GeminiAPI()
        self.memory_window = MEMORY_WINDOW_SIZE
        logger.debug("AIJournalingAssistant initialized")

    def chat(self, content: str, db) -> str:
        try:
            logger.debug(f"Processing chat request with content: {content[:100]}...")
            
            # Get recent entries for context
            recent_entries = self._get_recent_entries(db)
            logger.debug(f"Retrieved {len(recent_entries)} recent entries")
            
            # Build prompt with context
            prompt = self._build_prompt(content, recent_entries)
            logger.debug(f"Built prompt: {prompt[:100]}...")
            
            # Get AI response
            response = self.gemini_api.generate_response(prompt)
            logger.debug(f"Generated response: {response[:100]}...")
            
            return response
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise

    def _get_recent_entries(self, db) -> list:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.memory_window)
            entries = db.query(JournalEntry).filter(
                JournalEntry.created_at >= cutoff_date
            ).order_by(JournalEntry.created_at.desc()).all()
            return entries
        except Exception as e:
            logger.error(f"Error getting recent entries: {str(e)}", exc_info=True)
            return []

    def _build_prompt(self, content: str, recent_entries: list) -> str:
        try:
            context = "\n".join([
                f"Entry from {entry.created_at.strftime('%Y-%m-%d %H:%M')}: {entry.content}"
                for entry in recent_entries
            ])
            
            prompt = JOURNAL_PROMPT_TEMPLATE.format(
                context=context,
                current_entry=content
            )
            return prompt
        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}", exc_info=True)
            return JOURNAL_PROMPT_TEMPLATE.format(context="", current_entry=content)

    def generate_summary(self, db) -> str:
        try:
            logger.debug("Generating daily summary")
            
            # Get today's entries
            today = datetime.utcnow().date()
            entries = db.query(JournalEntry).filter(
                JournalEntry.created_at >= today
            ).order_by(JournalEntry.created_at.asc()).all()
            
            if not entries:
                logger.debug("No entries found for today")
                return "No entries found for today."
            
            # Build summary prompt
            entries_text = "\n".join([
                f"Entry from {entry.created_at.strftime('%H:%M')}: {entry.content}"
                for entry in entries
            ])
            
            prompt = SUMMARY_PROMPT_TEMPLATE.format(entries=entries_text)
            logger.debug(f"Built summary prompt: {prompt[:100]}...")
            
            # Generate summary
            summary = self.gemini_api.generate_response(prompt)
            logger.debug(f"Generated summary: {summary[:100]}...")
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            raise 