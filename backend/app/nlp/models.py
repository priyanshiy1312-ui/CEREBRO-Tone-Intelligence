"""Open-source HF models; falls back to lexicon heuristics if they cannot load (offline).
The active engine is reported in /api/health and in every response."""
import os, re
from functools import lru_cache

SENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMO_MODEL = "j-hartmann/emotion-english-distilroberta-base"
IRONY_MODEL = "cardiffnlp/twitter-roberta-base-irony"
EMOTIONS = ["anger", "frustration", "sadness", "joy", "fear", "surprise", "neutral"]

@lru_cache(maxsize=1)
def _pipes():
    if os.getenv("CEREBRO_LEXICON_ONLY") == "1": return None
    try:
        from transformers import pipeline
        mk = lambda m: pipeline("text-classification", model=m, top_k=None)
        return {"sent": mk(SENT_MODEL), "emo": mk(EMO_MODEL), "irony": mk(IRONY_MODEL)}
    except Exception as e:
        print("[cerebro] model load failed, using lexicon fallback:", e)
        return None

def engine(): return "transformers" if _pipes() else "lexicon-fallback"

NEG = set("never always apparently whatever fine ridiculous useless annoying hate stupid wrong blame fault ignore ignoring sick tired unfair worst waste pointless nobody nothing".split())
POS = set("thanks thank great love good nice awesome happy sure glad appreciate sorry perfect cool works yes please welcome".split())
ANGER = set("hate stupid ridiculous furious sick shut worst idiot damn".split())
FRUS = set("never always again apparently whatever ignoring tired listen annoying pointless".split())
def _toks(t): return re.findall(r"[a-z']+", t.lower())

def _lex_sent(t):
    w = _toks(t); n = sum(x in NEG for x in w); p = sum(x in POS for x in w)
    neg, pos = min(1, .15 + .3 * n), min(1, .15 + .3 * p); neu = max(.05, 1.3 - neg - pos)
    s = neg + pos + neu
    return {"negative": neg / s, "neutral": neu / s, "positive": pos / s}

def _lex_emo(t):
    w = _toks(t); sc = {e: .05 for e in EMOTIONS}; sc["neutral"] = .4
    sc["anger"] += .3 * sum(x in ANGER for x in w); sc["frustration"] += .25 * sum(x in FRUS for x in w)
    sc["joy"] += .3 * sum(x in POS for x in w); sc["sadness"] += .3 * sum(x in {"sad", "sorry", "alone", "miss"} for x in w)
    s = sum(sc.values())
    return {k: v / s for k, v in sc.items()}

def sentiment(texts):
    p = _pipes()
    if not p: return [_lex_sent(t) for t in texts]
    return [{d["label"].lower(): d["score"] for d in r} for r in p["sent"](texts, truncation=True)]

def emotion(texts):
    p = _pipes()
    if not p: return [_lex_emo(t) for t in texts]
    out = []
    for r in p["emo"](texts, truncation=True):
        d = {x["label"]: x["score"] for x in r}
        # The model has no 'frustration' label: approximated from anger/disgust mass (documented in README).
        e = {"anger": d.get("anger", 0) * .6, "frustration": d.get("anger", 0) * .4 + d.get("disgust", 0),
             "sadness": d.get("sadness", 0), "joy": d.get("joy", 0), "fear": d.get("fear", 0),
             "surprise": d.get("surprise", 0), "neutral": d.get("neutral", 0)}
        s = sum(e.values()) or 1
        out.append({k: v / s for k, v in e.items()})
    return out

def irony_base(texts):
    p = _pipes()
    if not p: return [None] * len(texts)
    return [next(x["score"] for x in r if x["label"].lower() in ("irony", "label_1")) for r in p["irony"](texts, truncation=True)]
