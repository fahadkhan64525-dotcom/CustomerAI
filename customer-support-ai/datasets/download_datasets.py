"""
Download Real Public Datasets
==============================
Downloads the actual public datasets referenced in the project guide.
Run: python datasets/download_datasets.py

Datasets downloaded:
  1. Banking77     — 77-intent customer query classification
  2. SQuAD v2.0    — Question answering (dev set)
  3. MS MARCO      — Semantic retrieval Q&A (sample)
"""

import os
import json
import urllib.request
import urllib.error

DATASETS_DIR = os.path.dirname(__file__)


def download(url: str, dest: str, label: str):
    if os.path.exists(dest):
        print(f"  ✅ {label} already downloaded — skipping.")
        return True
    print(f"  ⬇  Downloading {label} …")
    try:
        urllib.request.urlretrieve(url, dest)
        size_kb = os.path.getsize(dest) // 1024
        print(f"  ✅ {label} saved → {dest} ({size_kb} KB)")
        return True
    except urllib.error.URLError as e:
        print(f"  ⚠️  Failed to download {label}: {e}")
        print(f"      Download manually from: {url}")
        return False


def download_banking77():
    """
    Banking77 intent dataset (Hugging Face).
    77 banking-related intents — great for intent detection fine-tuning.
    """
    print("\n[1/3] Banking77 Intent Classification")
    base = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data"
    for split in ("train", "test"):
        download(
            f"{base}/{split}.csv",
            os.path.join(DATASETS_DIR, f"banking77_{split}.csv"),
            f"Banking77 {split}",
        )


def download_squad():
    """
    SQuAD 2.0 dev set (~4 MB).
    Useful for retrieval and answer generation evaluation.
    """
    print("\n[2/3] SQuAD 2.0 (dev set)")
    download(
        "https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json",
        os.path.join(DATASETS_DIR, "squad_dev_v2.json"),
        "SQuAD 2.0 dev",
    )


def download_msmarco_sample():
    """
    MS MARCO Q&A — downloads the small dev JSON (~12 MB).
    Large-scale question-answer pairs for semantic retrieval.
    """
    print("\n[3/3] MS MARCO (dev sample)")
    download(
        "https://msmarco.blob.core.windows.net/msmarco/dev_v2.1.json.gz",
        os.path.join(DATASETS_DIR, "msmarco_dev_sample.json.gz"),
        "MS MARCO dev",
    )
    # Decompress if gzip available
    gz_path = os.path.join(DATASETS_DIR, "msmarco_dev_sample.json.gz")
    out_path = gz_path.replace(".gz", "")
    if os.path.exists(gz_path) and not os.path.exists(out_path):
        import gzip, shutil
        with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"  ✅ Decompressed → {out_path}")


def show_summary():
    print("\n" + "="*55)
    print("DATASETS SUMMARY")
    print("="*55)
    files = [
        ("intent_classification.csv", "Custom 100-sample intent dataset"),
        ("customer_complaints.csv",   "25 realistic complaint records"),
        ("conversations.json",        "6 multi-turn dialogue examples"),
        ("qa_dataset.json",           "25 RAG evaluation Q&A pairs"),
        ("banking77_train.csv",       "Banking77 train (10,003 samples)"),
        ("banking77_test.csv",        "Banking77 test (3,080 samples)"),
        ("squad_dev_v2.json",         "SQuAD 2.0 dev (35,000+ questions)"),
        ("msmarco_dev_sample.json",   "MS MARCO dev Q&A pairs"),
    ]
    for fname, desc in files:
        path = os.path.join(DATASETS_DIR, fname)
        if os.path.exists(path):
            size = os.path.getsize(path)
            tag = f"{size/1024:.0f} KB" if size < 1_000_000 else f"{size/1_000_000:.1f} MB"
            print(f"  ✅  {fname:<35} {tag:<10}  {desc}")
        else:
            print(f"  ❌  {fname:<35} {'missing':<10}  {desc}")
    print()


if __name__ == "__main__":
    print("TechMart AI — Dataset Downloader")
    print("="*55)

    download_banking77()
    download_squad()
    download_msmarco_sample()
    show_summary()

    print("Done! Use these datasets for:")
    print("  • Intent classifier training → intent_classification.csv + banking77_train.csv")
    print("  • RAG evaluation             → qa_dataset.json + squad_dev_v2.json")
    print("  • Dialogue model training    → conversations.json")
    print("  • Semantic retrieval         → msmarco_dev_sample.json")
