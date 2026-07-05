"""
Test Suite — TechMart AI Customer Support Backend
Run: pytest tests/ -v
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Create a test client with a fresh in-memory database."""
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    os.environ["DB_PATH"] = ":memory:"

    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Health Check ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "TechMart" in data["service"]


# ── Authentication ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"username": "u1", "email": "dup@example.com", "password": "pass123"}
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json={**payload, "username": "u2"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "username": "loginuser", "email": "login@example.com", "password": "mypassword",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com", "password": "mypassword",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "username": "u3", "email": "u3@example.com", "password": "correct",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "u3@example.com", "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    reg = await client.post("/api/auth/register", json={
        "username": "meuser", "email": "me@example.com", "password": "pass123",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


# ── Chat ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_endpoint(client):
    """Chat should return a response with an agent field."""
    mock_result = {
        "response": "I can help with your billing inquiry.",
        "agent": MagicMock(value="billing"),
        "secondary_agents": [],
        "escalated": False,
        "sources": ["RefundPolicy.txt"],
        "reasoning": "billing intent detected",
    }
    with patch("backend.main.route_and_respond", new=AsyncMock(return_value=mock_result)):
        resp = await client.post("/api/chat", json={
            "message": "I was charged twice this month",
            "session_id": "test-session-001",
            "conversation_history": [],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "agent" in data
    assert "session_id" in data


@pytest.mark.asyncio
async def test_chat_history(client):
    resp = await client.get("/api/chat/history/nonexistent-session")
    assert resp.status_code == 200
    assert resp.json()["history"] == []


# ── Intent Detection ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intent_detection_billing():
    from backend.agents.router import detect_intent
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"primary_agent":"billing","secondary_agents":[],"confidence":0.95,"reasoning":"payment issue"}')]
    with patch("backend.agents.router.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        intent = await detect_intent("I was charged twice", [])
    assert intent.primary_agent.value == "billing"
    assert intent.confidence > 0.5


@pytest.mark.asyncio
async def test_intent_detection_technical():
    from backend.agents.router import detect_intent
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"primary_agent":"technical","secondary_agents":[],"confidence":0.9,"reasoning":"login issue"}')]
    with patch("backend.agents.router.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        intent = await detect_intent("I can't log into my account", [])
    assert intent.primary_agent.value == "technical"


@pytest.mark.asyncio
async def test_intent_fallback_on_error():
    from backend.agents.router import detect_intent
    with patch("backend.agents.router.client") as mock_client:
        mock_client.messages.create.side_effect = Exception("API error")
        intent = await detect_intent("some query", [])
    assert intent.primary_agent.value == "faq"  # fallback


# ── RAG Pipeline ───────────────────────────────────────────────────────────────

def test_chunk_text():
    from backend.rag.pipeline import chunk_text
    text = "A" * 1200
    chunks = chunk_text(text, "test.txt")
    assert len(chunks) > 1
    assert all("source" in c for c in chunks)
    assert all(len(c["text"]) <= 500 for c in chunks)


def test_chunk_text_short():
    from backend.rag.pipeline import chunk_text
    text = "Short text."
    chunks = chunk_text(text, "test.txt")
    assert len(chunks) == 1
    assert chunks[0]["source"] == "test.txt"


def test_vectorstore_empty_retrieve():
    from backend.rag.pipeline import VectorStore
    store = VectorStore()
    results = store.retrieve("billing issue")
    assert results == []


# ── Database ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_get_user():
    import os; os.environ["DB_PATH"] = ":memory:"
    from backend.database.db import init_db, create_user, get_user_by_email
    await init_db()
    user = await create_user("alice", "alice@test.com", "password123", "Alice")
    assert user["username"] == "alice"
    fetched = await get_user_by_email("alice@test.com")
    assert fetched is not None
    assert fetched["email"] == "alice@test.com"


@pytest.mark.asyncio
async def test_save_and_get_conversation():
    import os; os.environ["DB_PATH"] = ":memory:"
    from backend.database.db import init_db, save_conversation, get_conversation_history
    await init_db()
    session = "sess-abc-123"
    await save_conversation(session, "Hello", "Hi there!", "faq")
    history = await get_conversation_history(session)
    assert len(history) == 1
    assert history[0]["user_message"] == "Hello"
    assert history[0]["agent"] == "faq"


@pytest.mark.asyncio
async def test_analytics_empty():
    import os; os.environ["DB_PATH"] = ":memory:"
    from backend.database.db import init_db, get_analytics
    await init_db()
    data = await get_analytics()
    assert data["total_conversations"] == 0
    assert data["agent_usage"] == {}


# ── Password hashing ───────────────────────────────────────────────────────────

def test_password_hash_and_verify():
    from backend.database.db import hash_password, verify_password
    h = hash_password("mysecretpass")
    assert h != "mysecretpass"
    assert verify_password("mysecretpass", h)
    assert not verify_password("wrongpass", h)


def test_jwt_encode_decode():
    from backend.database.db import create_access_token, decode_token
    token = create_access_token({"sub": 42})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == 42


def test_invalid_jwt():
    from backend.database.db import decode_token
    assert decode_token("not.a.valid.token") is None


# ── Schemas ────────────────────────────────────────────────────────────────────

def test_agent_type_enum():
    from backend.models.schemas import AgentType
    assert AgentType.BILLING.value == "billing"
    assert AgentType.TECHNICAL.value == "technical"
    assert AgentType.COMPLAINT.value == "complaint"


def test_chat_response_schema():
    from backend.models.schemas import ChatResponse, AgentType
    from datetime import datetime
    r = ChatResponse(
        response="Test response",
        agent=AgentType.FAQ,
        session_id="abc",
        timestamp=datetime.utcnow(),
    )
    assert r.agent == AgentType.FAQ
    assert r.escalated is False
    assert r.sources == []
