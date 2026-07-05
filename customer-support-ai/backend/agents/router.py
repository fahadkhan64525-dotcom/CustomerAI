"""
Agent Router
============
Step 1 - Classify user intent with the LLM.
Step 2 - Route to the correct specialized agent(s).
Step 3 - If multiple agents are needed, run them and merge.
"""

import json
import os
from typing import List, Tuple

from backend.models.schemas import AgentType, IntentResult
from backend.rag.pipeline import get_vector_store

try:
    import anthropic
except ImportError:
    anthropic = None


def _build_client():
    if anthropic is None:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


client = _build_client()
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def _get_client():
    global client
    if client is None:
        client = _build_client()
    return client


INTENT_SYSTEM = """You are an intent classifier for a customer support system.
Your only job is to classify the user's message into one or more support categories
and return a JSON object (no markdown, no extra text).

Categories:
- billing    : payments, invoices, subscriptions, refunds, charges
- technical  : login issues, bugs, errors, installation, password reset
- product    : features, pricing, comparisons, availability
- complaint  : dissatisfaction, complaints, escalation requests
- faq        : general questions, company policies, contact info, hours

Return exactly:
{
  "primary_agent": "<category>",
  "secondary_agents": ["<category>", ...],
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}"""


async def detect_intent(message: str, history: List[dict]) -> IntentResult:
    """Use Claude to classify intent. Falls back to FAQ on error."""
    ctx_messages = history[-4:] if len(history) > 4 else history

    try:
        active_client = _get_client()
        if active_client is None:
            raise RuntimeError("Anthropic client is not configured.")

        response = active_client.messages.create(
            model=MODEL,
            max_tokens=256,
            system=INTENT_SYSTEM,
            messages=ctx_messages + [{"role": "user", "content": message}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        return IntentResult(
            primary_agent=AgentType(data["primary_agent"]),
            secondary_agents=[AgentType(agent) for agent in data.get("secondary_agents", [])],
            confidence=float(data.get("confidence", 0.8)),
            reasoning=data.get("reasoning", ""),
        )
    except Exception as exc:
        print(f"[Router] Intent detection error: {exc}")
        return IntentResult(
            primary_agent=AgentType.FAQ,
            secondary_agents=[],
            confidence=0.5,
            reasoning="Fallback - could not parse intent.",
        )


AGENT_PROMPTS = {
    AgentType.BILLING: """You are the Billing Support Agent for TechMart Electronics.
You specialize in: payment issues, invoices, subscription management, refunds, and billing disputes.
Be empathetic, professional, and solution-oriented.
If you cannot resolve an issue (e.g. manual refund needed), say so clearly and escalate.
Use the provided knowledge-base context when relevant.
Keep responses concise (3-5 sentences) unless more detail is truly needed.""",
    AgentType.TECHNICAL: """You are the Technical Support Agent for TechMart Electronics.
You specialize in: login/account issues, password reset, software installation, device errors, and bugs.
Guide users step-by-step. Number each step clearly.
If an issue requires engineering escalation, acknowledge the problem and set expectations.
Use the provided knowledge-base context when relevant.""",
    AgentType.PRODUCT: """You are the Product Information Agent for TechMart Electronics.
You specialize in: product features, pricing, availability, comparisons, and specifications.
Be enthusiastic but accurate. Never invent specifications.
Always suggest checking the TechMart website for the latest pricing.
Use the provided knowledge-base context when relevant.""",
    AgentType.COMPLAINT: """You are the Complaint Resolution Agent for TechMart Electronics.
You handle: customer dissatisfaction, service complaints, escalation requests, and feedback.
Acknowledge the customer's frustration sincerely. Apologize without admitting legal fault.
Propose concrete next steps. Escalate to a human agent if the customer requests it explicitly.
Use the provided knowledge-base context when relevant.""",
    AgentType.FAQ: """You are the FAQ & General Support Agent for TechMart Electronics.
You handle: company policies, general questions, contact information, store hours, and anything else.
Be friendly, helpful, and concise. If a question falls outside your knowledge, say so honestly.
Use the provided knowledge-base context when relevant.""",
}


async def call_agent(
    agent_type: AgentType,
    user_message: str,
    history: List[dict],
    rag_context: str = "",
) -> Tuple[str, bool]:
    """Call a specialized agent and return (response_text, is_escalated)."""
    system = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS[AgentType.FAQ])
    if rag_context:
        system += f"\n\n=== KNOWLEDGE BASE CONTEXT ===\n{rag_context}\n=== END CONTEXT ==="

    try:
        active_client = _get_client()
        if active_client is None:
            raise RuntimeError("Anthropic client is not configured.")

        response = active_client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=system,
            messages=history + [{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
        escalated = any(
            keyword in text.lower()
            for keyword in ["escalate", "human agent", "supervisor", "transfer you", "specialist"]
        )
        return text, escalated
    except Exception as exc:
        print(f"[{agent_type}] Agent call error: {exc}")
        return (
            "I apologize - I'm having trouble processing your request right now. "
            "Please try again or contact support@techmart.com.",
            False,
        )


async def route_and_respond(
    user_message: str,
    history: List[dict],
) -> dict:
    """
    Full pipeline:
      1. Detect intent
      2. Retrieve RAG context
      3. Call primary (and optional secondary) agents
      4. Merge responses if multi-agent
    """
    intent = await detect_intent(user_message, history)
    print(f"[Router] Intent: {intent.primary_agent} ({intent.confidence:.0%}) - {intent.reasoning}")

    store = get_vector_store()
    rag_context = store.format_context(user_message) if store.index else ""

    primary_response, escalated = await call_agent(
        intent.primary_agent, user_message, history, rag_context
    )

    secondary_responses = []
    for secondary_agent in intent.secondary_agents[:2]:
        if secondary_agent != intent.primary_agent:
            secondary_text, secondary_escalated = await call_agent(
                secondary_agent, user_message, history, rag_context
            )
            secondary_responses.append((secondary_agent, secondary_text))
            if secondary_escalated:
                escalated = True

    if secondary_responses:
        merged_parts = [f"**{intent.primary_agent.value.title()} Support:**\n{primary_response}"]
        for agent_type, text in secondary_responses:
            merged_parts.append(f"\n**{agent_type.value.title()} Support:**\n{text}")
        final_response = "\n\n".join(merged_parts)
    else:
        final_response = primary_response

    sources = []
    if rag_context:
        import re

        sources = list(set(re.findall(r"\[Source: ([^\]]+)\]", rag_context)))

    return {
        "response": final_response,
        "agent": intent.primary_agent,
        "secondary_agents": intent.secondary_agents,
        "escalated": escalated,
        "sources": sources,
        "reasoning": intent.reasoning,
    }
