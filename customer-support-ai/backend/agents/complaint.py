"""
Complaint Resolution Agent
==========================
Specializes in: complaints, dissatisfaction, escalation.
"""

from backend.agents.router import call_agent
from backend.models.schemas import AgentType


async def handle(user_message: str, history: list, rag_context: str = "") -> tuple[str, bool]:
    return await call_agent(AgentType.COMPLAINT, user_message, history, rag_context)


ESCALATION_CONTACTS = {
    "email":   "complaints@techmart.com",
    "phone":   "1-800-TECHMART (Mon–Fri, 9am–6pm EST)",
    "chat":    "Live chat available on techmart.com/support",
    "twitter": "@TechMartSupport",
}

COMPENSATION_TIERS = {
    "minor":    "10% discount on next purchase",
    "moderate": "Free shipping + 20% discount",
    "major":    "Full refund or product replacement + loyalty credit",
}
