"""
Billing Agent
=============
Specializes in: payments, invoices, subscriptions, refunds, billing disputes.
"""

from backend.agents.router import call_agent
from backend.models.schemas import AgentType


async def handle(user_message: str, history: list, rag_context: str = "") -> tuple[str, bool]:
    """Entry point for the billing agent."""
    return await call_agent(AgentType.BILLING, user_message, history, rag_context)


# Billing-specific utilities

REFUND_POLICY_SUMMARY = """
TechMart Electronics Refund Policy (summary):
- Electronics: 30-day return window from delivery date.
- Software/digital products: non-refundable once activated.
- Defective items: full refund or replacement within 90 days.
- Process: Submit refund request via account portal or email billing@techmart.com.
- Refund timeline: 5–10 business days to original payment method.
"""

SUBSCRIPTION_TIERS = {
    "basic":    {"price": "$9.99/mo",  "features": ["1 device", "Basic support", "5 GB cloud"]},
    "premium":  {"price": "$19.99/mo", "features": ["3 devices", "Priority support", "50 GB cloud"]},
    "business": {"price": "$49.99/mo", "features": ["Unlimited devices", "24/7 support", "500 GB cloud"]},
}


def get_subscription_info(tier: str) -> dict:
    return SUBSCRIPTION_TIERS.get(tier.lower(), {})
