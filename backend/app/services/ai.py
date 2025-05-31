from datetime import datetime, date
from typing import Dict, List, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
from sqlalchemy.orm import Session

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
            
            # Save summary to database
            daily_summary = DailySummary(
                date=date.today(),
                summary=summary
            )
            db.add(daily_summary)
            db.commit()
            
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {e}" 