"""
FAQ & General Support Agent
===========================
Specializes in: company policies, general questions, contact info.
"""

from backend.agents.router import call_agent
from backend.models.schemas import AgentType


async def handle(user_message: str, history: list, rag_context: str = "") -> tuple[str, bool]:
    return await call_agent(AgentType.FAQ, user_message, history, rag_context)


COMPANY_INFO = {
    "name":         "TechMart Electronics",
    "founded":      "2010",
    "headquarters": "San Francisco, CA",
    "support_email":"support@techmart.com",
    "support_phone":"1-800-TECHMART",
    "hours":        "Mon–Fri 9am–6pm EST, Sat 10am–4pm EST",
    "website":      "https://www.techmart.com",
    "social": {
        "twitter":   "@TechMartHQ",
        "instagram": "@TechMartElectronics",
        "linkedin":  "linkedin.com/company/techmart-electronics",
    },
}

POLICIES_SUMMARY = {
    "shipping":  "Free standard shipping on orders over $50. Express (2-day) available for $9.99.",
    "warranty":  "1-year limited warranty on all products. Extended warranty available for purchase.",
    "privacy":   "We never sell personal data. See techmart.com/privacy for full policy.",
    "returns":   "30-day hassle-free returns on hardware. See refund policy for details.",
    "security":  "All transactions use 256-bit SSL encryption. PCI-DSS compliant.",
}
