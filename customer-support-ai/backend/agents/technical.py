"""
Technical Support Agent
=======================
Specializes in: login, password reset, installation, errors, bugs.
"""

from backend.agents.router import call_agent
from backend.models.schemas import AgentType


async def handle(user_message: str, history: list, rag_context: str = "") -> tuple[str, bool]:
    return await call_agent(AgentType.TECHNICAL, user_message, history, rag_context)


# Common technical solutions knowledge

COMMON_SOLUTIONS = {
    "login_failed": [
        "Clear browser cache and cookies, then try again.",
        "Try an incognito/private browser window.",
        "Reset your password via the 'Forgot Password' link.",
        "Disable browser extensions that might block scripts.",
        "Check that Caps Lock is off.",
    ],
    "installation_error": [
        "Run the installer as Administrator (right-click → Run as admin).",
        "Disable antivirus temporarily during installation.",
        "Ensure you have at least 2 GB free disk space.",
        "Download a fresh copy of the installer if the file is corrupted.",
        "Check system requirements: Windows 10+, macOS 12+, or Ubuntu 20.04+.",
    ],
    "slow_performance": [
        "Restart the application.",
        "Check for available software updates.",
        "Close background applications to free RAM.",
        "Clear the application cache: Settings → Advanced → Clear Cache.",
        "Reinstall if the issue persists after the above steps.",
    ],
}


def get_common_solution(issue_type: str) -> list:
    return COMMON_SOLUTIONS.get(issue_type, [])
