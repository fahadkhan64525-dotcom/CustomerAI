"""
TechMart AI Customer Support - FastAPI Backend
==============================================
Run: uvicorn backend.main:app --reload --port 8000
"""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

from backend.agents.router import route_and_respond
from backend.database.db import (
    create_access_token,
    create_user,
    decode_token,
    get_analytics,
    get_conversation_history,
    get_user_by_email,
    get_user_by_id,
    init_db,
    save_conversation,
    verify_password,
)
from backend.models.schemas import (
    AgentType,
    AnalyticsResponse,
    ChatRequest,
    ChatResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from backend.rag.pipeline import initialize_rag


def _normalize_agent(agent: object) -> AgentType:
    if isinstance(agent, AgentType):
        return agent

    agent_value = getattr(agent, "value", agent)
    if isinstance(agent_value, AgentType):
        return agent_value

    return AgentType(str(agent_value))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await initialize_rag()
    yield


app = FastAPI(
    title="TechMart AI Customer Support",
    description="Multi-Agent AI Customer Support System with RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return await get_user_by_id(payload.get("sub"))


@app.post("/api/auth/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister):
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = await create_user(body.username, body.email, body.password, body.full_name)
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=datetime.fromisoformat(user["created_at"]),
        ),
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = await get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["hashed_pw"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=datetime.fromisoformat(user["created_at"]),
        ),
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        created_at=datetime.fromisoformat(current_user["created_at"]),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user),
):
    session_id = body.session_id or str(uuid.uuid4())
    start_ms = time.time()

    history = [
        {"role": turn["role"], "content": turn["content"]}
        for turn in body.conversation_history
        if turn.get("role") in ("user", "assistant")
    ]

    result = await route_and_respond(body.message, history)
    primary_agent = _normalize_agent(result["agent"])
    secondary_agents = [
        _normalize_agent(agent)
        for agent in result.get("secondary_agents", [])
        if agent is not None
    ]

    elapsed_ms = int((time.time() - start_ms) * 1000)

    user_id = current_user["id"] if current_user else None
    await save_conversation(
        session_id=session_id,
        user_message=body.message,
        ai_response=result["response"],
        agent=primary_agent.value,
        user_id=user_id,
        escalated=result.get("escalated", False),
        response_ms=elapsed_ms,
    )

    return ChatResponse(
        response=result["response"],
        agent=primary_agent,
        secondary_agents=secondary_agents,
        session_id=session_id,
        sources=result.get("sources", []),
        escalated=result.get("escalated", False),
    )


@app.get("/api/chat/history/{session_id}")
async def history(session_id: str, limit: int = 20):
    records = await get_conversation_history(session_id, limit)
    return {"session_id": session_id, "history": records}


@app.get("/api/analytics", response_model=AnalyticsResponse)
async def analytics(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    data = await get_analytics()
    return AnalyticsResponse(**data)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TechMart AI Support", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
