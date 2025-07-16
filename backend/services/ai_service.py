import os
import json
from typing import List
from datetime import datetime
from openai import OpenAI
from textblob import TextBlob
from models.interaction import Interaction, InteractionSummary

class AIService:
    """Service for AI-powered interaction analysis"""
    
    def __init__(self):
        print(f"API KEY: {os.getenv('OPENAI_API_KEY')}")
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def summarize_interactions(self, interactions: List[Interaction]) -> InteractionSummary:
        """Generate AI summary of interactions"""
        try:
            # Prepare interaction data for AI processing
            interaction_text = self._prepare_interaction_text(interactions)
            
            # Generate summary using OpenAI
            summary = self._generate_summary(interaction_text)
            
            # Extract key topics
            key_topics = self._extract_key_topics(interaction_text)
            
            # Analyze sentiment
            sentiment_score = self._analyze_sentiment(interaction_text)
            
            # Predict next steps
            next_steps = self._predict_next_steps(interaction_text, summary)
            
            # Determine urgency level
            urgency_level = self._determine_urgency(interactions, sentiment_score)
            
            # Create date range
            date_range = self._create_date_range(interactions)
            
            return InteractionSummary(
                account_id=interactions[0].account_id,
                summary=summary,
                key_topics=key_topics,
                sentiment_score=sentiment_score,
                next_steps=next_steps,
                total_interactions=len(interactions),
                date_range=date_range,
                urgency_level=urgency_level
            )
            
        except Exception as e:
            raise Exception(f"Error generating interaction summary: {str(e)}")
    
    def _prepare_interaction_text(self, interactions: List[Interaction]) -> str:
        """Prepare interaction data for AI processing"""
        text_parts = []
        for interaction in interactions:
            text_parts.append(f"""
            Date: {interaction.created_date}
            Type: {interaction.interaction_type}
            Subject: {interaction.subject}
            Description: {interaction.description}
            Created by: {interaction.created_by}
            Status: {interaction.status or 'N/A'}
            ---
            """)
        return "\n".join(text_parts)
    
    def _generate_summary(self, interaction_text: str) -> str:
        """Generate summary using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes customer interactions for sales teams. Provide concise, actionable summaries focusing on key discussion points, decisions made, and customer concerns."
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following customer interactions:\n\n{interaction_text}"
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _extract_key_topics(self, interaction_text: str) -> List[str]:
        """Extract key topics from interactions"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract 3-5 key topics from customer interactions. Return only the topics as a comma-separated list."
                    },
                    {
                        "role": "user",
                        "content": f"Extract key topics from:\n\n{interaction_text}"
                    }
                ],
                max_tokens=100,
                temperature=0.2
            )
            topics = response.choices[0].message.content.strip().split(',')
            return [topic.strip() for topic in topics[:5]]
        except Exception as e:
            return ["Error extracting topics"]
    
    def _analyze_sentiment(self, interaction_text: str) -> float:
        """Analyze sentiment of interactions"""
        try:
            blob = TextBlob(interaction_text)
            return round(blob.sentiment.polarity, 2)
        except Exception as e:
            return 0.0
    
    def _predict_next_steps(self, interaction_text: str, summary: str) -> List[str]:
        """Predict next steps based on interactions"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Based on customer interactions, suggest 2-4 specific next steps the sales team should take. Be actionable and specific."
                    },
                    {
                        "role": "user",
                        "content": f"Based on this summary: {summary}\n\nAnd these interactions: {interaction_text}\n\nWhat should be the next steps?"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            next_steps_text = response.choices[0].message.content.strip()
            # Parse the response into individual steps
            steps = []
            for line in next_steps_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    # Clean up formatting
                    step = line.lstrip('- •0123456789. ')
                    if step:
                        steps.append(step)
            
            return steps[:4] if steps else ["Follow up with customer"]
            
        except Exception as e:
            return ["Error predicting next steps"]
    
    def _determine_urgency(self, interactions: List[Interaction], sentiment_score: float) -> str:
        """Determine urgency level based on interactions"""
        # Check for urgent keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        recent_interactions = [i for i in interactions if (datetime.now() - i.created_date).days <= 7]
        
        has_urgent_keywords = any(
            any(keyword in (interaction.subject + ' ' + interaction.description).lower() 
                for keyword in urgent_keywords)
            for interaction in interactions
        )
        
        if has_urgent_keywords or sentiment_score < -0.3:
            return "High"
        elif len(recent_interactions) >= 3 or sentiment_score < 0:
            return "Medium"
        else:
            return "Low"
    
    def _create_date_range(self, interactions: List[Interaction]) -> str:
        """Create date range string for interactions"""
        if not interactions:
            return "No interactions"
        
        dates = [interaction.created_date for interaction in interactions]
        min_date = min(dates)
        max_date = max(dates)
        
        if min_date.date() == max_date.date():
            return min_date.strftime("%Y-%m-%d")
        else:
            return f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
