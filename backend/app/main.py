"""Main entry point for the AI Journaling Assistant"""

import os
import sys
from datetime import date
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, journal, mood, summary, insights
from app.database import engine, Base
from app.models import user, journal as journal_model, mood as mood_model
from app.assistant import AIJournalingAssistant

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Journaling Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(journal.router, prefix="/journal", tags=["journal"])
app.include_router(mood.router, prefix="/mood", tags=["mood"])
app.include_router(summary.router, prefix="/summary", tags=["summary"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Journaling Assistant API"}

def get_api_key() -> Optional[str]:
    """Get the API key from environment or user input"""
    from config import GEMINI_API_KEY
    
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
        
    print("\n🔑 Enter your Google API key: ", end="")
    api_key = input().strip()
    return api_key if api_key else None


def get_user_settings() -> tuple[int, float]:
    """Get user settings for the assistant"""
    print("\n⚙️  Optional settings (press Enter for defaults):")
    
    # Get max tokens
    while True:
        max_tokens_input = input("Max tokens per response (default: 512): ").strip()
        if not max_tokens_input:
            max_tokens = 512
            break
        try:
            max_tokens = int(max_tokens_input)
            if max_tokens > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get temperature
    while True:
        temperature_input = input("Temperature 0.0-1.0 (default: 0.7): ").strip()
        if not temperature_input:
            temperature = 0.7
            break
        try:
            temperature = float(temperature_input)
            if 0.0 <= temperature <= 1.0:
                break
            print("Please enter a number between 0.0 and 1.0.")
        except ValueError:
            print("Please enter a valid number.")
        
    return max_tokens, temperature


def print_welcome() -> None:
    """Print welcome message and instructions"""
    print("\n🌟 Welcome to your AI Journaling Assistant!")
    print("=" * 50)
    print("💭 How to use:")
    print("   • Just start typing to journal about your day")
    print("   • Type 'summarize today' for a daily summary")
    print("   • Type 'stats' to see your journaling statistics")
    print("   • Type 'quit' or 'exit' to end the session")
    print("=" * 50)


def print_stats(stats: dict) -> None:
    """Print journaling statistics"""
    print(f"\n📊 Journal Statistics:")
    print(f"   📅 Days with entries: {stats['total_days']}")
    print(f"   💬 Total conversations: {stats['total_exchanges']}")
    print(f"   📝 Daily summaries: {stats['total_summaries']}")
    
    if stats.get('recent_dates'):
        print(f"\n🕒 Recent activity:")
        for date_str in stats['recent_dates']:
            print(f"   {date_str}")


def main() -> None:
    """Main function to run the AI Journaling Assistant"""
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Get user settings
    max_tokens, temperature = get_user_settings()
    
    print("\n🚀 Initializing with Gemini model...")
    print("This may take a moment...")
    
    # Initialize the assistant
    try:
        assistant = AIJournalingAssistant(
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature
        )
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        return
    
    # Show welcome message
    print_welcome()
    
    # Main chat loop
    try:
        while True:
            print(f"\n📅 {date.today().strftime('%B %d, %Y')}")
            user_input = input("\n💭 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for journaling today! Take care!")
                break
            elif user_input.lower() == 'stats':
                stats = assistant.get_stats()
                print_stats(stats)
                continue
            
            # Process the input
            print("\n🤖 Assistant: ", end="", flush=True)
            response = assistant.chat(user_input)
            print(response)
            
    except KeyboardInterrupt:
        print("\n\n👋 Session ended. Your conversations are saved!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    main() 