from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Interaction:
    """Model representing a Salesforce Interaction record"""
    id: str
    account_id: str
    subject: str
    description: str
    interaction_type: str
    created_date: datetime
    created_by: str
    status: Optional[str] = None
    priority: Optional[str] = None

@dataclass
class InteractionSummary:
    """Model for AI-generated interaction summary"""
    account_id: str
    summary: str
    key_topics: List[str]
    sentiment_score: float
    next_steps: List[str]
    total_interactions: int
    date_range: str
    urgency_level: str

@dataclass
class SummarizeRequest:
    """Request model for summarization endpoint"""
    account_id: str
    interactions: List[Interaction]
    
@dataclass
class SummarizeResponse:
    """Response model for summarization endpoint"""
    success: bool
    summary: InteractionSummary
    error_message: Optional[str] = None
