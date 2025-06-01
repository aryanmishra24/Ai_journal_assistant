class AIJournalingAssistant:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4-turbo-preview"
        self.system_prompt = """You are a compassionate AI journaling companion. Your role is to help users reflect on their thoughts, feelings, and experiences through journaling. You should:
        1. Be empathetic and understanding
        2. Encourage self-reflection
        3. Help users identify patterns and insights
        4. Maintain a supportive and non-judgmental tone
        5. Respect user privacy and confidentiality
        6. Provide gentle guidance when appropriate
        7. Focus on emotional well-being and personal growth
        8. Avoid giving direct advice unless specifically asked
        9. Help users process their emotions and experiences
        10. Create a safe space for honest expression

        When generating summaries:
        - Focus on emotional patterns and themes
        - Highlight significant insights and realizations
        - Note any recurring thoughts or feelings
        - Identify potential areas for growth
        - Maintain a compassionate and supportive tone
        - Keep summaries concise but meaningful
        - Use natural, conversational language
        - Avoid clinical or overly analytical language
        - Respect the user's emotional journey
        - Celebrate progress and positive moments"""

    def _generate_journal_summary(self, db: Session, entries: List[JournalEntry]) -> str:
        """Generate a summary of journal entries."""
        if not entries:
            return "No entries to summarize."

        # Sort entries by creation time
        sorted_entries = sorted(entries, key=lambda x: x.created_at)
        
        # Format entries for the prompt
        entries_text = "\n\n".join([
            f"Entry {i+1} ({entry.created_at.strftime('%I:%M %p')}):\n{entry.content}"
            for i, entry in enumerate(sorted_entries)
        ])

        prompt = f"""Please provide a concise summary of the following journal entries, focusing on the main themes, emotions, and insights:

{entries_text}

Summary:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating journal summary: {str(e)}")
            return "Unable to generate summary at this time."

    def _generate_mood_summary(self, db: Session, moods: List[Mood]) -> str:
        """Generate a summary of mood entries."""
        if not moods:
            return "No mood entries to summarize."

        # Sort entries by creation time
        sorted_moods = sorted(moods, key=lambda x: x.created_at)
        
        # Calculate average mood
        avg_mood = sum(mood.mood_score for mood in moods) / len(moods)
        
        # Get mood distribution
        mood_distribution = {}
        for mood in moods:
            label = mood.mood_label
            mood_distribution[label] = mood_distribution.get(label, 0) + 1

        # Format entries for the prompt
        entries_text = "\n\n".join([
            f"Entry {i+1} ({mood.created_at.strftime('%I:%M %p')}):\n"
            f"Mood: {mood.mood_score}/10 - {mood.mood_label}\n"
            f"Notes: {mood.notes if mood.notes else 'No notes'}"
            for i, mood in enumerate(sorted_moods)
        ])

        prompt = f"""Please provide a concise summary of the following mood entries, focusing on emotional patterns, significant changes, and overall well-being:

Average Mood: {avg_mood:.1f}/10
Mood Distribution: {', '.join(f'{label}: {count}' for label, count in mood_distribution.items())}

Entries:
{entries_text}

Summary:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating mood summary: {str(e)}")
            return "Unable to generate summary at this time."

    def _generate_insights(self, db: Session, entries: List[JournalEntry], moods: List[Mood]) -> str:
        """Generate insights from journal and mood entries."""
        if not entries and not moods:
            return "No entries to analyze."

        # Format entries for the prompt
        journal_text = "\n\n".join([
            f"Journal Entry {i+1} ({entry.created_at.strftime('%I:%M %p')}):\n{entry.content}"
            for i, entry in enumerate(entries)
        ]) if entries else "No journal entries."

        mood_text = "\n\n".join([
            f"Mood Entry {i+1} ({mood.created_at.strftime('%I:%M %p')}):\n"
            f"Mood: {mood.mood_score}/10 - {mood.mood_label}\n"
            f"Notes: {mood.notes if mood.notes else 'No notes'}"
            for i, mood in enumerate(moods)
        ]) if moods else "No mood entries."

        prompt = f"""Please analyze the following journal and mood entries to provide insights about patterns, emotional well-being, and potential areas for growth:

Journal Entries:
{journal_text}

Mood Entries:
{mood_text}

Insights:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return "Unable to generate insights at this time." 