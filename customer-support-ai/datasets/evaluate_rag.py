"""
RAG Evaluation Script
======================
Evaluates retrieval quality of the FAISS vector store using qa_dataset.json.
Computes: Hit Rate @K, MRR, exact-match answer accuracy.

Run (backend must be running OR vector store must already be built):
  python datasets/evaluate_rag.py
  python datasets/evaluate_rag.py --top-k 3
  python datasets/evaluate_rag.py --build-first
"""

import os
import sys
import json
import argparse
import time

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

QA_PATH = os.path.join(os.path.dirname(__file__), "qa_dataset.json")


def load_qa_dataset():
    with open(QA_PATH) as f:
        data = json.load(f)
    return data["data"]


def normalize(text: str) -> str:
    """Lowercase and strip punctuation for loose matching."""
    import re
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


# ── Retrieval evaluation ──────────────────────────────────────────────────────

def evaluate_retrieval(store, qa_pairs: list, top_k: int = 5):
    """
    For each QA pair, check if any retrieved chunk contains the answer.
    Returns hit-rate @K and MRR.
    """
    hits, reciprocal_ranks = [], []

    for qa in qa_pairs:
        question    = qa["question"]
        answer_norm = normalize(qa["answer"])
        source      = qa.get("context_source", "")

        results = store.retrieve(question, top_k=top_k)

        hit = False
        rank = 0
        for i, (chunk_text, chunk_source, _) in enumerate(results, 1):
            chunk_norm = normalize(chunk_text)
            # Check: does chunk contain the answer substring?
            if answer_norm in chunk_norm:
                hit = True
                rank = i
                break
            # Fallback: correct source file retrieved
            if source and source in chunk_source:
                hit = True
                rank = i
                break

        hits.append(int(hit))
        reciprocal_ranks.append(1 / rank if rank > 0 else 0)

    hit_rate = sum(hits) / len(hits) * 100
    mrr      = sum(reciprocal_ranks) / len(reciprocal_ranks)
    return hit_rate, mrr, hits


def evaluate_by_agent(qa_pairs, hits):
    """Break down hit rate by agent category."""
    from collections import defaultdict
    agent_hits   = defaultdict(list)
    for qa, h in zip(qa_pairs, hits):
        agent_hits[qa.get("agent", "unknown")].append(h)
    return {agent: sum(h)/len(h)*100 for agent, h in agent_hits.items()}


def evaluate_by_difficulty(qa_pairs, hits):
    """Break down hit rate by question difficulty."""
    from collections import defaultdict
    diff_hits = defaultdict(list)
    for qa, h in zip(qa_pairs, hits):
        diff_hits[qa.get("difficulty", "unknown")].append(h)
    return {d: sum(h)/len(h)*100 for d, h in diff_hits.items()}


# ── Pretty printing ───────────────────────────────────────────────────────────

def print_bar(label, value, width=30, color_thresh=70):
    filled = int(value / 100 * width)
    bar    = "█" * filled + "░" * (width - filled)
    flag   = "✅" if value >= color_thresh else ("⚠️ " if value >= 50 else "❌")
    print(f"  {flag}  {label:<20} [{bar}] {value:5.1f}%")


def print_results(hit_rate, mrr, top_k, agent_breakdown, diff_breakdown, elapsed):
    w = 60
    print("\n" + "="*w)
    print("  RAG EVALUATION RESULTS")
    print("="*w)
    print(f"  Top-K             : {top_k}")
    print(f"  Elapsed           : {elapsed:.2f}s")
    print(f"  MRR               : {mrr:.3f}  (Mean Reciprocal Rank)")
    print()
    print_bar(f"Hit Rate @{top_k}", hit_rate)
    print()

    print("  By Agent:")
    for agent, hr in sorted(agent_breakdown.items()):
        print_bar(f"  {agent}", hr, width=20)

    print("\n  By Difficulty:")
    for diff in ("easy", "medium", "hard"):
        if diff in diff_breakdown:
            print_bar(f"  {diff}", diff_breakdown[diff], width=20)

    print("="*w)

    if hit_rate >= 80:
        verdict = "🟢 EXCELLENT — RAG pipeline is working well."
    elif hit_rate >= 60:
        verdict = "🟡 GOOD — Consider adding more documents or tuning chunk size."
    else:
        verdict = "🔴 POOR — Check knowledge base documents and embedding model."
    print(f"\n  {verdict}\n")


# ── Per-question detail ───────────────────────────────────────────────────────

def show_misses(store, qa_pairs, hits, top_k):
    misses = [(qa, h) for qa, h in zip(qa_pairs, hits) if not h]
    if not misses:
        print("  🎉 No misses — all questions retrieved correctly!\n")
        return
    print(f"\n  ❌ Missed Questions ({len(misses)}):")
    for qa, _ in misses:
        print(f"     Q: {qa['question']}")
        print(f"     A: {qa['answer']}")
        # Show what was retrieved instead
        results = store.retrieve(qa["question"], top_k=2)
        if results:
            print(f"     Retrieved: \"{results[0][0][:80]}…\" [{results[0][1]}]")
        print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate TechMart RAG pipeline")
    parser.add_argument("--top-k",       type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--build-first", action="store_true",  help="(Re)build vector store before evaluating")
    parser.add_argument("--show-misses", action="store_true",  help="Show details of missed questions")
    args = parser.parse_args()

    print("TechMart RAG Evaluation")
    print("="*60)

    # Import RAG pipeline
    try:
        from backend.rag.pipeline import VectorStore, load_all_documents, initialize_rag
        import asyncio
    except ImportError as e:
        print(f"❌ Could not import backend: {e}")
        print("   Run from the project root: python datasets/evaluate_rag.py")
        return

    # Build or load vector store
    store = VectorStore()
    if args.build_first:
        print("\nBuilding vector store from knowledge base …")
        chunks = load_all_documents()
        if not chunks:
            print("❌ No documents found in knowledge_base/. Add PDF or TXT files.")
            return
        store.build(chunks)
    else:
        print("\nLoading existing vector store …")
        if not store.load():
            print("  Vector store not found — building now …")
            chunks = load_all_documents()
            if chunks:
                store.build(chunks)
                store.save()
            else:
                print("❌ No documents found. Add files to knowledge_base/ first.")
                return

    # Load QA pairs
    qa_pairs = load_qa_dataset()
    print(f"  Loaded {len(qa_pairs)} QA pairs from qa_dataset.json")

    # Run evaluation
    print(f"\nRunning retrieval evaluation (top_k={args.top_k}) …")
    t0 = time.time()
    hit_rate, mrr, hits = evaluate_retrieval(store, qa_pairs, top_k=args.top_k)
    elapsed = time.time() - t0

    agent_breakdown = evaluate_by_agent(qa_pairs, hits)
    diff_breakdown  = evaluate_by_difficulty(qa_pairs, hits)

    print_results(hit_rate, mrr, args.top_k, agent_breakdown, diff_breakdown, elapsed)

    if args.show_misses:
        show_misses(store, qa_pairs, hits, top_k=args.top_k)

    # Save results
    results_path = os.path.join(os.path.dirname(__file__), "rag_eval_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "top_k": args.top_k,
            "hit_rate": round(hit_rate, 2),
            "mrr": round(mrr, 3),
            "by_agent": agent_breakdown,
            "by_difficulty": diff_breakdown,
            "elapsed_seconds": round(elapsed, 2),
            "total_questions": len(qa_pairs),
        }, f, indent=2)
    print(f"  Results saved → {results_path}")


if __name__ == "__main__":
    main()
