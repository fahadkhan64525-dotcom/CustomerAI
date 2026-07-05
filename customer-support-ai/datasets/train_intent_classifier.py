"""
Intent Classifier — Train & Evaluate
======================================
Trains a lightweight sklearn classifier on intent_classification.csv
and optionally on the Banking77 dataset.

Run:
  python datasets/train_intent_classifier.py
  python datasets/train_intent_classifier.py --dataset banking77
  python datasets/train_intent_classifier.py --eval-only
"""

import os
import json
import argparse
import csv
import pickle
from collections import Counter

# ── Optional heavy imports (installed via requirements.txt) ──────────────────
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.pipeline import Pipeline
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    print("⚠️  scikit-learn not installed. Run: pip install scikit-learn")

DATASETS_DIR  = os.path.dirname(__file__)
MODELS_DIR    = os.path.join(os.path.dirname(DATASETS_DIR), "backend", "models")
MODEL_PATH    = os.path.join(MODELS_DIR, "intent_classifier.pkl")
LABEL_MAP_PATH = os.path.join(MODELS_DIR, "intent_labels.json")


# ── Data loading ─────────────────────────────────────────────────────────────

def load_custom_dataset():
    path = os.path.join(DATASETS_DIR, "intent_classification.csv")
    texts, agents = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            agents.append(row["agent"])     # 5-class: billing/technical/product/complaint/faq
    print(f"  Loaded custom dataset: {len(texts)} samples")
    return texts, agents


def load_banking77():
    path = os.path.join(DATASETS_DIR, "banking77_train.csv")
    if not os.path.exists(path):
        print("  ⚠️  banking77_train.csv not found. Run download_datasets.py first.")
        return [], []
    texts, labels = [], []
    # Banking77 maps fine-grained intents → our 5 agents
    billing_kws   = {"balance","charge","refund","payment","bill","invoice","subscription","transfer","fund","fee","loan","mortgage","savings","interest","limit","cashback","top_up"}
    technical_kws = {"login","password","pin","app","card_arrival","card_blocked","card_cancelled","card_linking","card_not_working","lost_card","stolen_card","contactless"}
    product_kws   = {"exchange_rate","currency","travel","abroad","atm","cash","apple_pay","google_pay","crypto","card_about"}
    complaint_kws = {"complaint","dispute","fraud","scam","phishing"}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            intent = row.get("label", row.get("category", "")).lower()
            text   = row.get("text", "")
            if not text:
                continue
            # Map to our 5 agents
            if any(k in intent for k in billing_kws):
                agent = "billing"
            elif any(k in intent for k in technical_kws):
                agent = "technical"
            elif any(k in intent for k in product_kws):
                agent = "product"
            elif any(k in intent for k in complaint_kws):
                agent = "complaint"
            else:
                agent = "faq"
            texts.append(text)
            labels.append(agent)
    print(f"  Loaded Banking77: {len(texts)} samples")
    return texts, labels


# ── Training ─────────────────────────────────────────────────────────────────

def train(texts, labels):
    print("\n  Building TF-IDF + Logistic Regression pipeline …")
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=15_000,
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            solver="lbfgs",
            multi_class="multinomial",
        )),
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print(f"  Training on {len(X_train)} samples …")
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    acc = (np.array(y_pred) == np.array(y_test)).mean()
    print(f"\n  ✅ Test Accuracy: {acc:.1%}")
    print("\n" + classification_report(y_test, y_pred))

    # Cross-validation
    cv_scores = cross_val_score(pipeline, texts, labels, cv=5, scoring="accuracy")
    print(f"  5-Fold CV Accuracy: {cv_scores.mean():.1%} ± {cv_scores.std():.1%}")

    return pipeline


def save_model(pipeline, labels):
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    unique_labels = sorted(set(labels))
    with open(LABEL_MAP_PATH, "w") as f:
        json.dump(unique_labels, f)
    print(f"\n  ✅ Model saved → {MODEL_PATH}")
    print(f"  ✅ Labels saved → {LABEL_MAP_PATH}")


def load_model():
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    with open(LABEL_MAP_PATH) as f:
        labels = json.load(f)
    return pipeline, labels


# ── Inference helper ─────────────────────────────────────────────────────────

def predict(pipeline, texts):
    preds  = pipeline.predict(texts)
    probas = pipeline.predict_proba(texts)
    return [
        {"text": t, "predicted_agent": p, "confidence": float(max(pr))}
        for t, p, pr in zip(texts, preds, probas)
    ]


# ── Demo evaluation ──────────────────────────────────────────────────────────

DEMO_QUERIES = [
    "I was charged twice this month",
    "Can't log into my account",
    "What laptops do you sell?",
    "This is completely unacceptable, I want a refund",
    "What are your store hours?",
    "My software keeps crashing",
    "Do you have a student discount?",
    "I want to speak to a manager",
    "How long does shipping take?",
    "My payment failed at checkout",
]

def run_demo(pipeline):
    print("\n" + "="*55)
    print("DEMO — Agent Routing Predictions")
    print("="*55)
    results = predict(pipeline, DEMO_QUERIES)
    for r in results:
        bar = "█" * int(r["confidence"] * 20)
        print(f"  {r['predicted_agent']:12s} [{r['confidence']:.0%}] {bar:<20}  \"{r['text']}\"")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not SKLEARN_OK:
        return

    parser = argparse.ArgumentParser(description="Train TechMart intent classifier")
    parser.add_argument("--dataset", choices=["custom", "banking77", "combined"], default="combined")
    parser.add_argument("--eval-only", action="store_true", help="Skip training, load saved model")
    args = parser.parse_args()

    print("TechMart Intent Classifier")
    print("="*55)

    if args.eval_only:
        if not os.path.exists(MODEL_PATH):
            print(f"❌ No saved model found at {MODEL_PATH}. Train first.")
            return
        print("Loading saved model …")
        pipeline, _ = load_model()
        run_demo(pipeline)
        return

    # Load data
    print("\nLoading datasets …")
    all_texts, all_labels = [], []

    if args.dataset in ("custom", "combined"):
        t, l = load_custom_dataset()
        all_texts += t; all_labels += l

    if args.dataset in ("banking77", "combined"):
        t, l = load_banking77()
        all_texts += t; all_labels += l

    if not all_texts:
        print("❌ No data loaded. Exiting."); return

    print(f"\n  Total samples: {len(all_texts)}")
    print(f"  Class distribution: {dict(Counter(all_labels))}")

    # Train
    pipeline = train(all_texts, all_labels)
    save_model(pipeline, all_labels)
    run_demo(pipeline)


if __name__ == "__main__":
    main()
