"""
Product Information Agent
=========================
Specializes in: features, pricing, comparisons, availability.
"""

from backend.agents.router import call_agent
from backend.models.schemas import AgentType


async def handle(user_message: str, history: list, rag_context: str = "") -> tuple[str, bool]:
    return await call_agent(AgentType.PRODUCT, user_message, history, rag_context)


PRODUCT_CATALOG = {
    "TechMart Pro X1": {
        "category": "Laptop",
        "price": "$1,299",
        "specs": {"CPU": "Intel Core i7-13th Gen", "RAM": "16 GB", "Storage": "512 GB SSD", "Display": '15.6" 4K'},
        "in_stock": True,
    },
    "TechMart Wireless Hub": {
        "category": "Networking",
        "price": "$149",
        "specs": {"WiFi": "Wi-Fi 6E", "Ports": "4x Ethernet, 2x USB-A", "Range": "up to 3,000 sq ft"},
        "in_stock": True,
    },
    "TechMart SmartWatch S3": {
        "category": "Wearable",
        "price": "$299",
        "specs": {"Display": "AMOLED 1.4\"", "Battery": "7 days", "Water": "IP68"},
        "in_stock": False,
    },
}
