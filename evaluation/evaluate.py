"""Benchmark evaluation. These numbers come from LABELED files you provide; they are NOT demo predictions.
Usage: python evaluation/evaluate.py labeled.csv   (columns: text,sentiment[,emotion,sarcasm(0/1)])"""
import sys, csv
sys.path.insert(0, "backend")
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from app.nlp import models, tone

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
texts = [r["text"] for r in rows]
S, E, I = models.sentiment(texts), models.emotion(texts), models.irony_base(texts)
print("engine:", models.engine())
y = [r["sentiment"] for r in rows]; p = [max(s, key=s.get) for s in S]
print("SENTIMENT\n", classification_report(y, p, zero_division=0))
print(confusion_matrix(y, p, labels=["negative", "neutral", "positive"]))
if "emotion" in rows[0]:
    y = [r["emotion"] for r in rows]; p = [max(e, key=e.get) for e in E]
    print("EMOTION\n", classification_report(y, p, zero_division=0))
if "sarcasm" in rows[0]:
    y = [int(r["sarcasm"]) for r in rows]
    p = [int(tone.analyze(t, s, i, 0)[0]["sarcasm"] >= .5) for t, s, i in zip(texts, S, I)]
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
    print(f"SARCASM P={pr:.2f} R={rc:.2f} F1={f1:.2f}")
print("Escalation: label whole conversations escalating/not, compare with /api/analyze escalation.detected.")
