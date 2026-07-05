# TechMart AI — Datasets

This folder contains all datasets used for training, evaluation, and testing
of the Multi-Agent AI Customer Support System.

---

## Folder Contents

```
datasets/
├── intent_classification.csv      # Custom intent dataset (100 samples)
├── customer_complaints.csv        # Realistic complaint records (25 samples)
├── conversations.json             # Multi-turn dialogue examples (6 convos)
├── qa_dataset.json                # RAG evaluation Q&A pairs (25 questions)
│
├── download_datasets.py           # Download real public datasets
├── train_intent_classifier.py     # Train sklearn intent classifier
├── evaluate_rag.py                # Evaluate RAG retrieval quality
├── analyze_datasets.py            # Generate statistics report
│
└── README.md                      # This file
```

After running `download_datasets.py`, you also get:
```
├── banking77_train.csv            # 10,003 banking intent samples
├── banking77_test.csv             # 3,080 banking intent samples
├── squad_dev_v2.json              # 35,000+ QA pairs (SQuAD 2.0)
└── msmarco_dev_sample.json        # MS MARCO Q&A pairs
```

---

## Dataset Descriptions

### 1. `intent_classification.csv` — Custom Intent Dataset

| Column  | Description |
|---------|-------------|
| `text`  | Customer query text |
| `label` | Fine-grained intent label (e.g. `refund_request`, `login_issue`) |
| `agent` | Target agent: `billing`, `technical`, `product`, `complaint`, `faq` |

**100 samples** across 5 agent categories and 30+ intent labels.

**Use for:**
- Training the agent router
- Few-shot examples in LLM prompts
- Intent detection evaluation

---

### 2. `customer_complaints.csv` — Complaints Dataset

| Column | Description |
|--------|-------------|
| `complaint_id` | Unique ID |
| `category` | Domain: billing, technical, product, complaint, faq |
| `sub_category` | Specific issue type |
| `complaint_text` | Raw customer complaint |
| `resolution` | How the issue was resolved |
| `agent_assigned` | Which agent handled it |
| `escalated` | True/False — was it escalated to human? |
| `resolution_time_hours` | Time to resolve |
| `satisfaction_score` | 1–5 customer rating |

**25 samples** with realistic scenarios, resolutions, and metrics.

**Use for:**
- Testing complaint and escalation agent logic
- Simulating edge cases
- Analytics dashboard data
- Evaluating response quality

---

### 3. `conversations.json` — Multi-Turn Dialogues

Each conversation object:
```json
{
  "conversation_id": "conv_001",
  "category": "billing",
  "turns": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "...", "agent": "billing"}
  ],
  "resolved": true,
  "escalated": false,
  "satisfaction": 5
}
```

**6 conversations** covering: billing, technical, complaint, product, multi-agent, FAQ.

**Use for:**
- Few-shot examples in agent system prompts
- Testing multi-turn conversation memory
- Dialogue model evaluation
- Demo scripts

---

### 4. `qa_dataset.json` — RAG Evaluation Dataset

Each QA pair:
```json
{
  "id": "qa_001",
  "question": "What is the return window for hardware products?",
  "answer": "30 days from the delivery date",
  "context_source": "RefundPolicy.txt",
  "agent": "billing",
  "difficulty": "easy"
}
```

**25 questions** at easy/medium/hard difficulty, sourced from the TechMart knowledge base.

**Use for:**
- Evaluating RAG retrieval (run `evaluate_rag.py`)
- Measuring Hit Rate @K and MRR
- Identifying gaps in the knowledge base

---

### 5. Banking77 (Public — download separately)

- **10,003 training** / **3,080 test** samples
- **77 banking-related intents**
- Source: [PolyAI Banking77](https://github.com/PolyAI-LDN/task-specific-datasets)

```bash
python datasets/download_datasets.py
```

**Use for:**
- Large-scale intent classifier training
- Combined with custom dataset for better generalization

---

### 6. SQuAD 2.0 (Public — download separately)

- **35,000+ question-answer pairs**
- Source: [rajpurkar/SQuAD-explorer](https://github.com/rajpurkar/SQuAD-explorer)

**Use for:**
- Large-scale RAG evaluation
- Answer extraction model training

---

### 7. MS MARCO (Public — download separately)

- Large-scale semantic Q&A
- Source: [microsoft/MSMARCO](https://github.com/microsoft/MSMARCO-Question-Answering)

**Use for:**
- Semantic retrieval benchmarking
- Training dense retrieval models

---

## Running the Scripts

### Download real public datasets
```bash
python datasets/download_datasets.py
```

### Analyze all datasets (statistics report)
```bash
python datasets/analyze_datasets.py
```

### Train the intent classifier
```bash
# Train on custom data only
python datasets/train_intent_classifier.py --dataset custom

# Train on Banking77 only
python datasets/train_intent_classifier.py --dataset banking77

# Train on both (recommended)
python datasets/train_intent_classifier.py --dataset combined
```

### Evaluate RAG retrieval quality
```bash
# Must have backend vectorstore built first (start the backend server once)
python datasets/evaluate_rag.py

# Rebuild vectorstore before evaluating
python datasets/evaluate_rag.py --build-first

# Show which questions were missed
python datasets/evaluate_rag.py --show-misses

# Change top-K
python datasets/evaluate_rag.py --top-k 3
```

---

## Evaluation Metrics

### Intent Classification
| Metric | Target |
|--------|--------|
| Accuracy (test set) | > 85% |
| 5-Fold CV Accuracy | > 80% |
| Per-class F1 | > 0.75 |

### RAG Retrieval
| Metric | Description | Target |
|--------|-------------|--------|
| Hit Rate @5 | % of questions where answer found in top-5 chunks | > 80% |
| Hit Rate @1 | % where answer is in the top-1 chunk | > 50% |
| MRR | Mean Reciprocal Rank | > 0.60 |

---

## Adding Your Own Data

### Add more intent examples
Append rows to `intent_classification.csv`:
```csv
"I need a tax receipt for my purchase",get_invoice,billing
"The app crashes when I open settings",app_crash,technical
```

### Add more QA pairs for RAG evaluation
Append to `qa_dataset.json` `data` array:
```json
{
  "id": "qa_026",
  "question": "Your question here",
  "answer": "Expected answer",
  "context_source": "FAQ.txt",
  "agent": "faq",
  "difficulty": "easy"
}
```

### Add more knowledge base documents
Place PDF or TXT files in `knowledge_base/` and restart the backend to re-index.
