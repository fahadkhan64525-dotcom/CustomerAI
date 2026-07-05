"""
Dataset Analysis & Statistics
==============================
Generates a full statistical report of all datasets in the datasets/ folder.
Run: python datasets/analyze_datasets.py

Output:
  - Console report
  - datasets/analysis_report.json
"""

import os
import json
import csv
from collections import Counter, defaultdict
from datetime import datetime

DATASETS_DIR = os.path.dirname(__file__)


# ── Loaders ───────────────────────────────────────────────────────────────────

def analyze_intent_csv():
    path = os.path.join(DATASETS_DIR, "intent_classification.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    agents  = Counter(r["agent"]  for r in rows)
    intents = Counter(r["label"]  for r in rows)
    avg_len = sum(len(r["text"]) for r in rows) / len(rows)

    return {
        "file": "intent_classification.csv",
        "total_samples": len(rows),
        "unique_intents": len(intents),
        "agent_distribution": dict(agents),
        "top_intents": dict(intents.most_common(10)),
        "avg_text_length_chars": round(avg_len, 1),
        "classes": sorted(agents.keys()),
    }


def analyze_complaints_csv():
    path = os.path.join(DATASETS_DIR, "customer_complaints.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    categories  = Counter(r["category"]          for r in rows)
    agents      = Counter(r["agent_assigned"]     for r in rows)
    escalated   = sum(1 for r in rows if r["escalated"].lower() == "true")
    resolved    = sum(1 for r in rows if r["resolution"])
    scores      = [int(r["satisfaction_score"]) for r in rows if r.get("satisfaction_score")]
    avg_score   = sum(scores) / len(scores) if scores else 0
    res_times   = [int(r["resolution_time_hours"]) for r in rows if r.get("resolution_time_hours")]
    avg_res     = sum(res_times) / len(res_times) if res_times else 0

    return {
        "file": "customer_complaints.csv",
        "total_samples": len(rows),
        "resolved": resolved,
        "escalated": escalated,
        "escalation_rate_pct": round(escalated / len(rows) * 100, 1),
        "category_distribution": dict(categories),
        "agent_distribution": dict(agents),
        "avg_satisfaction_score": round(avg_score, 2),
        "avg_resolution_time_hours": round(avg_res, 1),
    }


def analyze_conversations_json():
    path = os.path.join(DATASETS_DIR, "conversations.json")
    with open(path) as f:
        convos = json.load(f)

    categories     = Counter(c["category"]    for c in convos)
    escalated      = sum(1 for c in convos if c.get("escalated"))
    resolved       = sum(1 for c in convos if c.get("resolved"))
    turns_counts   = [len(c["turns"]) for c in convos]
    avg_turns      = sum(turns_counts) / len(turns_counts)
    scores         = [c["satisfaction"] for c in convos if c.get("satisfaction")]
    avg_score      = sum(scores) / len(scores) if scores else 0
    agents_used    = Counter(
        t.get("agent")
        for c in convos for t in c["turns"]
        if t["role"] == "assistant" and t.get("agent")
    )

    return {
        "file": "conversations.json",
        "total_conversations": len(convos),
        "resolved": resolved,
        "escalated": escalated,
        "category_distribution": dict(categories),
        "agents_used": dict(agents_used),
        "avg_turns_per_conversation": round(avg_turns, 1),
        "avg_satisfaction": round(avg_score, 2),
        "total_turns": sum(turns_counts),
    }


def analyze_qa_json():
    path = os.path.join(DATASETS_DIR, "qa_dataset.json")
    with open(path) as f:
        data = json.load(f)
    items = data["data"]

    agents      = Counter(q["agent"]      for q in items)
    difficulties = Counter(q["difficulty"] for q in items)
    sources     = Counter(q["context_source"] for q in items)
    q_lens      = [len(q["question"]) for q in items]
    a_lens      = [len(q["answer"])   for q in items]

    return {
        "file": "qa_dataset.json",
        "version": data.get("version"),
        "total_qa_pairs": len(items),
        "agent_distribution": dict(agents),
        "difficulty_distribution": dict(difficulties),
        "source_distribution": dict(sources),
        "avg_question_length": round(sum(q_lens) / len(q_lens), 1),
        "avg_answer_length": round(sum(a_lens) / len(a_lens), 1),
    }


def analyze_banking77(split="train"):
    path = os.path.join(DATASETS_DIR, f"banking77_{split}.csv")
    if not os.path.exists(path):
        return {"file": f"banking77_{split}.csv", "status": "not downloaded"}
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    labels = Counter(r.get("label", r.get("category", "")) for r in rows)
    return {
        "file": f"banking77_{split}.csv",
        "total_samples": len(rows),
        "unique_intents": len(labels),
        "top_intents": dict(labels.most_common(5)),
    }


# ── Printer ───────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*58}")
    print(f"  {title}")
    print(f"{'='*58}")


def kv(label, value, indent=4):
    pad = " " * indent
    if isinstance(value, dict):
        print(f"{pad}{label}:")
        for k, v in value.items():
            print(f"{pad}  {k:25s}: {v}")
    else:
        print(f"{pad}{label:30s}: {value}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n🔍  TechMart Dataset Analysis Report")
    print(f"    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = {}

    # 1. Intent Classification CSV
    section("1. Intent Classification Dataset")
    r = analyze_intent_csv()
    kv("Total samples",       r["total_samples"])
    kv("Unique intents",      r["unique_intents"])
    kv("Avg text length",     f"{r['avg_text_length_chars']} chars")
    kv("Agent distribution",  r["agent_distribution"])
    kv("Top intents (5)",     dict(list(r["top_intents"].items())[:5]))
    all_results["intent_classification"] = r

    # 2. Customer Complaints
    section("2. Customer Complaints Dataset")
    r = analyze_complaints_csv()
    kv("Total complaints",       r["total_samples"])
    kv("Resolved",               r["resolved"])
    kv("Escalated",              f"{r['escalated']} ({r['escalation_rate_pct']}%)")
    kv("Avg satisfaction",       f"{r['avg_satisfaction_score']} / 5")
    kv("Avg resolution time",    f"{r['avg_resolution_time_hours']} hours")
    kv("Category distribution",  r["category_distribution"])
    all_results["customer_complaints"] = r

    # 3. Conversations
    section("3. Multi-Turn Conversations Dataset")
    r = analyze_conversations_json()
    kv("Total conversations",    r["total_conversations"])
    kv("Total turns",            r["total_turns"])
    kv("Avg turns / convo",      r["avg_turns_per_conversation"])
    kv("Resolved",               r["resolved"])
    kv("Escalated",              r["escalated"])
    kv("Avg satisfaction",       f"{r['avg_satisfaction']} / 5")
    kv("Agents used",            r["agents_used"])
    all_results["conversations"] = r

    # 4. QA Dataset
    section("4. RAG Evaluation QA Dataset")
    r = analyze_qa_json()
    kv("Version",                r["version"])
    kv("Total QA pairs",         r["total_qa_pairs"])
    kv("Avg question length",    f"{r['avg_question_length']} chars")
    kv("Avg answer length",      f"{r['avg_answer_length']} chars")
    kv("By agent",               r["agent_distribution"])
    kv("By difficulty",          r["difficulty_distribution"])
    kv("By source",              r["source_distribution"])
    all_results["qa_dataset"] = r

    # 5. Banking77 (if downloaded)
    section("5. Banking77 Dataset (Public)")
    for split in ("train", "test"):
        r = analyze_banking77(split)
        if r.get("status") == "not downloaded":
            print(f"    ⚠️  banking77_{split}.csv not found.")
            print(f"       Run: python datasets/download_datasets.py")
        else:
            kv(f"{split} samples",       r["total_samples"])
            kv(f"{split} unique intents", r["unique_intents"])
        all_results[f"banking77_{split}"] = r

    # Summary
    section("SUMMARY — How to Use Each Dataset")
    uses = {
        "intent_classification.csv": "Fine-tune/evaluate agent router — sklearn or LLM few-shot",
        "banking77_train.csv":       "Large-scale intent training set (10k+ samples)",
        "customer_complaints.csv":   "Test complaint agent, escalation logic, satisfaction scoring",
        "conversations.json":        "Few-shot examples in agent system prompts / dialogue eval",
        "qa_dataset.json":           "Evaluate RAG: run evaluate_rag.py to get Hit Rate & MRR",
        "squad_dev_v2.json":         "Large-scale QA evaluation (35k questions)",
        "msmarco_dev_sample.json":   "Semantic retrieval benchmark",
    }
    for fname, use in uses.items():
        exists = "✅" if os.path.exists(os.path.join(DATASETS_DIR, fname)) else "❌"
        print(f"  {exists}  {fname:<35}  {use}")

    # Save report
    out = os.path.join(DATASETS_DIR, "analysis_report.json")
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  📄 Full report saved → {out}\n")


if __name__ == "__main__":
    main()
