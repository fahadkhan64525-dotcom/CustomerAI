import os
from typing import Optional, Set

import aiosqlite
from jose import JWTError, jwt
from passlib.context import CryptContext

MEMORY_DB_URI = "file:techmart-support-ai?mode=memory&cache=shared"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_memory_keeper: Optional[aiosqlite.Connection] = None
_initialized_targets: Set[str] = set()


def get_db_path() -> str:
    return os.getenv("DB_PATH", "support_ai.db")


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")


def is_in_memory_db(db_path: Optional[str] = None) -> bool:
    return (db_path or get_db_path()) == ":memory:"


def _get_target_key(db_path: Optional[str] = None) -> str:
    return MEMORY_DB_URI if is_in_memory_db(db_path) else (db_path or get_db_path())


async def _ensure_memory_keeper() -> aiosqlite.Connection:
    global _memory_keeper
    if _memory_keeper is None:
        _memory_keeper = await aiosqlite.connect(MEMORY_DB_URI, uri=True)
    return _memory_keeper


async def _open_connection() -> aiosqlite.Connection:
    db_path = get_db_path()
    if is_in_memory_db(db_path):
        await _ensure_memory_keeper()
        return await aiosqlite.connect(MEMORY_DB_URI, uri=True)
    return await aiosqlite.connect(db_path)


CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    UNIQUE NOT NULL,
    email       TEXT    UNIQUE NOT NULL,
    full_name   TEXT    DEFAULT '',
    hashed_pw   TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now'))
)
"""

CREATE_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS conversations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT    NOT NULL,
    user_id       INTEGER,
    user_message  TEXT    NOT NULL,
    ai_response   TEXT    NOT NULL,
    agent         TEXT    NOT NULL,
    escalated     INTEGER DEFAULT 0,
    response_ms   INTEGER DEFAULT 0,
    created_at    TEXT    DEFAULT (datetime('now'))
)
"""

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT    PRIMARY KEY,
    user_id     INTEGER,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT (datetime('now'))
)
"""


async def _ensure_schema(reset: bool = False):
    db_path = get_db_path()
    target_key = _get_target_key(db_path)

    if not reset and target_key in _initialized_targets:
        return

    db = await _open_connection()
    async with db:
        if reset and is_in_memory_db(db_path):
            await db.execute("DROP TABLE IF EXISTS conversations")
            await db.execute("DROP TABLE IF EXISTS sessions")
            await db.execute("DROP TABLE IF EXISTS users")
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CONVERSATIONS)
        await db.execute(CREATE_SESSIONS)
        await db.commit()

    _initialized_targets.add(target_key)


async def init_db():
    """Initialize the SQLite database."""
    await _ensure_schema(reset=is_in_memory_db())
    print("Database initialized.")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    return jwt.encode(data.copy(), get_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        return None


async def create_user(username: str, email: str, password: str, full_name: str = "") -> dict:
    await _ensure_schema()
    hashed = hash_password(password)
    db = await _open_connection()
    async with db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "INSERT INTO users (username, email, full_name, hashed_pw) VALUES (?, ?, ?, ?)",
            (username, email, full_name, hashed),
        )
        await db.commit()
        row = await db.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
        return dict(await row.fetchone())


async def get_user_by_email(email: str) -> Optional[dict]:
    await _ensure_schema()
    db = await _open_connection()
    async with db:
        db.row_factory = aiosqlite.Row
        row = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = await row.fetchone()
        return dict(result) if result else None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    await _ensure_schema()
    db = await _open_connection()
    async with db:
        db.row_factory = aiosqlite.Row
        row = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = await row.fetchone()
        return dict(result) if result else None


async def save_conversation(
    session_id: str,
    user_message: str,
    ai_response: str,
    agent: str,
    user_id: Optional[int] = None,
    escalated: bool = False,
    response_ms: int = 0,
) -> int:
    await _ensure_schema()
    db = await _open_connection()
    async with db:
        cursor = await db.execute(
            """INSERT INTO conversations
               (session_id, user_id, user_message, ai_response, agent, escalated, response_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, user_message, ai_response, agent, int(escalated), response_ms),
        )
        await db.commit()
        return cursor.lastrowid


async def get_conversation_history(session_id: str, limit: int = 20) -> list:
    await _ensure_schema()
    db = await _open_connection()
    async with db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute(
            """SELECT * FROM conversations
               WHERE session_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, limit),
        )
        results = await rows.fetchall()
        return [dict(row) for row in reversed(results)]


async def get_analytics() -> dict:
    await _ensure_schema()
    db = await _open_connection()
    async with db:
        db.row_factory = aiosqlite.Row

        total = await (await db.execute("SELECT COUNT(*) as c FROM conversations")).fetchone()
        agents = await (await db.execute(
            "SELECT agent, COUNT(*) as cnt FROM conversations GROUP BY agent ORDER BY cnt DESC"
        )).fetchall()
        avg_ms = await (await db.execute(
            "SELECT AVG(response_ms) as avg FROM conversations"
        )).fetchone()
        escalated = await (await db.execute(
            "SELECT COUNT(*) as c FROM conversations WHERE escalated = 1"
        )).fetchone()

        agent_usage = {row["agent"]: row["cnt"] for row in agents}
        total_count = total["c"] if total else 0
        escalation_rate = (escalated["c"] / total_count * 100) if total_count > 0 else 0

        return {
            "total_conversations": total_count,
            "agent_usage": agent_usage,
            "avg_response_time_ms": round(avg_ms["avg"] or 0, 1),
            "escalation_rate": round(escalation_rate, 1),
            "top_intents": list(agent_usage.keys())[:5],
        }
