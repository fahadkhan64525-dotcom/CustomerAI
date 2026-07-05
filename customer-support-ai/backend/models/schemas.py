from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class AgentType(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    PRODUCT = "product"
    COMPLAINT = "complaint"
    FAQ = "faq"
    ORCHESTRATOR = "orchestrator"


class IntentResult(BaseModel):
    primary_agent: AgentType
    secondary_agents: List[AgentType] = Field(default_factory=list)
    confidence: float
    reasoning: str


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    agent: Optional[AgentType] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_history: List[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    agent: AgentType
    secondary_agents: List[AgentType] = Field(default_factory=list)
    session_id: str
    sources: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    escalated: bool = False


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConversationRecord(BaseModel):
    id: Optional[int] = None
    session_id: str
    user_id: Optional[int] = None
    user_message: str
    ai_response: str
    agent: AgentType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    escalated: bool = False


class AnalyticsResponse(BaseModel):
    total_conversations: int
    agent_usage: dict
    avg_response_time_ms: float
    escalation_rate: float
    top_intents: List[str]
