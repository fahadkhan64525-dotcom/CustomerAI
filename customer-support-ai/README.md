# TechMart AI Customer Support System
**Multi-Agent AI Customer Support using RAG and LLMs**

A production-grade capstone project implementing a Multi-Agent AI Customer Support system with Retrieval-Augmented Generation (RAG), FastAPI backend, React frontend, and Claude (Anthropic) as the LLM.

---

## Architecture Overview

```
Customer (Web Chat UI)
        │
        ▼
  React Frontend (Next.js + Tailwind)
        │  REST API calls
        ▼
  FastAPI Backend (Python)
        │
   ┌────┴────────────────┐
   ▼                     ▼
Intent Detection    Conversation Memory
   (Claude LLM)       (SQLite DB)
        │
        ▼
   Agent Router
        │
 ┌──────┼──────┬──────┬──────┐
 ▼      ▼      ▼      ▼      ▼
Billing Tech  Product Complaint FAQ
Agent   Agent  Agent   Agent  Agent
        │
        ▼
  RAG Pipeline (FAISS + sentence-transformers)
        │
        ▼
  Knowledge Base (PDFs/TXT files)
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js, Next.js 14, Tailwind CSS, Axios |
| Backend | Python 3.11, FastAPI, Uvicorn |
| LLM | Anthropic Claude (claude-sonnet-4-6) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS |
| Database | SQLite (aiosqlite) |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Vercel (frontend) + Railway/Render (backend) |

---

## Project Structure

```
customer-support-ai/
├── backend/
│   ├── agents/
│   │   ├── router.py        # Intent detection + multi-agent orchestration
│   │   ├── billing.py       # Payment/invoice/refund agent
│   │   ├── technical.py     # Login/bug/installation agent
│   │   ├── product.py       # Features/pricing/availability agent
│   │   ├── complaint.py     # Escalation/dissatisfaction agent
│   │   └── faq.py           # General policies/FAQ agent
│   ├── rag/
│   │   └── pipeline.py      # Document loading, chunking, embedding, retrieval
│   ├── database/
│   │   └── db.py            # SQLite CRUD + auth helpers
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response schemas
│   └── main.py              # FastAPI app entry point
├── frontend/
│   ├── components/          # React components
│   ├── pages/               # Next.js pages
│   ├── hooks/               # Custom React hooks
│   ├── services/
│   │   └── api.js           # API client
│   └── styles/              # Tailwind CSS
├── knowledge_base/
│   ├── FAQ.txt
│   ├── RefundPolicy.txt
│   ├── Pricing.txt
│   ├── UserManual.txt
│   └── Warranty.txt
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- An Anthropic API key (get one at console.anthropic.com)

### 1 — Clone and configure

```bash
git clone https://github.com/your-repo/customer-support-ai.git
cd customer-support-ai

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here
```

### 2 — Backend setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

On first start, the server will:
1. Initialize the SQLite database
2. Load knowledge base documents
3. Generate embeddings and build the FAISS vector index
4. Save the index for subsequent fast starts

### 3 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open http://localhost:3000

### 4 — Add your own knowledge base

Drop PDF or TXT files into the `knowledge_base/` folder, then restart the backend to re-index.

```bash
# Force re-index by deleting cached vectorstore
rm -rf backend/vectorstore/
uvicorn backend.main:app --reload --port 8000
```

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/auth/me` | Get current user |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message, get AI response |
| GET | `/api/chat/history/{session_id}` | Get conversation history |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics` | Usage stats (authenticated) |

### POST /api/chat

Request:
```json
{
  "message": "I was charged twice for my subscription",
  "session_id": "abc-123",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

Response:
```json
{
  "response": "I'm sorry to hear about the duplicate charge...",
  "agent": "billing",
  "secondary_agents": [],
  "session_id": "abc-123",
  "sources": ["RefundPolicy.txt", "FAQ.txt"],
  "escalated": false,
  "timestamp": "2024-07-01T12:00:00"
}
```

---

## Agent Routing Examples

| User Query | Primary Agent | Secondary Agent |
|-----------|---------------|-----------------|
| "I was charged twice" | billing | — |
| "Can't log in after paying" | technical | billing |
| "What are your laptop specs?" | product | — |
| "This is unacceptable, I want a manager" | complaint | — |
| "What are your store hours?" | faq | — |
| "Paid for premium but features locked" | billing | technical |

---

## RAG Pipeline

1. **Load** — PDFs and TXT files are read from `knowledge_base/`
2. **Chunk** — Documents split into 500-char overlapping chunks
3. **Embed** — Each chunk encoded with `all-MiniLM-L6-v2`
4. **Index** — Embeddings stored in FAISS for fast ANN search
5. **Retrieve** — Top-5 semantically similar chunks fetched per query
6. **Augment** — Retrieved context prepended to the agent's system prompt
7. **Generate** — Claude generates a grounded response

---

## Deployment

### Backend (Railway or Render)
```bash
# Set environment variables in Railway/Render dashboard
# Deploy from GitHub or with Railway CLI:
railway up
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL to your Railway/Render backend URL
```

### Database (Production)
For production, replace SQLite with PostgreSQL or MongoDB Atlas:
- Update `backend/database/db.py` to use `asyncpg` or `motor`
- Set `DATABASE_URL` in environment variables

---

## Evaluation

| Component | Points | Description |
|-----------|--------|-------------|
| Frontend Design | 10 | Responsive chat UI, agent indicators, auth flow |
| Backend APIs | 15 | FastAPI, auth, session management, error handling |
| Multi-Agent Architecture | 20 | Intent detection, routing, 5 specialized agents |
| RAG Implementation | 20 | Chunking, FAISS indexing, semantic retrieval |
| LLM Integration | 15 | Claude integration, prompt engineering |
| Database Design | 10 | SQLite schema, conversation history, analytics |
| Documentation & Deployment | 10 | README, API docs, deployment config |
| **Total** | **100** | |

---

## Bonus Features Implemented
- [x] Multi-agent parallel invocation (e.g., billing + technical)
- [x] Escalation detection from AI responses
- [x] Analytics dashboard endpoint
- [x] Source attribution from RAG retrieval
- [x] JWT authentication with session management
- [ ] Voice interface (bonus extension)
- [ ] Multilingual support (bonus extension)
- [ ] WhatsApp/Email integration (bonus extension)

---

## License
MIT License — for educational purposes.
