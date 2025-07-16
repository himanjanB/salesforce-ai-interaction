import os
from typing import List
from datetime import datetime
from textblob import TextBlob
from openai import OpenAI

from models.interaction import Interaction, InteractionSummary

class AIService:
    """Service for AI-powered interaction analysis using OpenAI v1.x"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=api_key)

    def summarize_interactions(self, interactions: List[Interaction]) -> InteractionSummary:
        try:
            interaction_text = self._prepare_interaction_text(interactions)
            summary = self._generate_summary(interaction_text)
            key_topics = self._extract_key_topics(interaction_text)
            sentiment_score = self._analyze_sentiment(interaction_text)
            next_steps = self._predict_next_steps(interaction_text, summary)
            urgency_level = self._determine_urgency(interactions, sentiment_score)
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
        return "\n".join([
            f"""
            Date: {i.created_date}
            Type: {i.interaction_type}
            Subject: {i.subject}
            Description: {i.description}
            Created by: {i.created_by}
            Status: {i.status or 'N/A'}
            ---
            """
            for i in interactions
        ])

    def _generate_summary(self, interaction_text: str) -> str:
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
            content = response.choices[0].message.content.strip()
            return [topic.strip() for topic in content.split(",") if topic.strip()]
        except Exception as e:
            return [f"Error extracting topics: {str(e)}"]

    def _analyze_sentiment(self, interaction_text: str) -> float:
        try:
            blob = TextBlob(interaction_text)
            return round(blob.sentiment.polarity, 2)
        except Exception:
            return 0.0

    def _predict_next_steps(self, interaction_text: str, summary: str) -> List[str]:
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
                        "content": (
                            f"Based on this summary: {summary}\n\n"
                            f"And these interactions: {interaction_text}\n\n"
                            "What should be the next steps?"
                        )
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            lines = content.split("\n")
            steps = []
            for line in lines:
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                    step = line.lstrip("-•0123456789. ").strip()
                    if step:
                        steps.append(step)
            return steps[:4] if steps else ["Follow up with customer"]
        except Exception as e:
            return [f"Error predicting next steps: {str(e)}"]

    def _determine_urgency(self, interactions: List[Interaction], sentiment_score: float) -> str:
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        recent = [i for i in interactions if (datetime.now() - i.created_date).days <= 7]

        has_urgency = any(
            any(kw in (i.subject + ' ' + i.description).lower() for kw in urgent_keywords)
            for i in interactions
        )

        if has_urgency or sentiment_score < -0.3:
            return "High"
        elif len(recent) >= 3 or sentiment_score < 0:
            return "Medium"
        else:
            return "Low"

    def _create_date_range(self, interactions: List[Interaction]) -> str:
        if not interactions:
            return "No interactions"
        dates = [i.created_date for i in interactions]
        min_d, max_d = min(dates), max(dates)
        return min_d.strftime("%Y-%m-%d") if min_d == max_d else f"{min_d.strftime('%Y-%m-%d')} to {max_d.strftime('%Y-%m-%d')}"