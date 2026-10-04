"""Conversation-level engine: tone trajectory, conflict, escalation, turning point, triggers."""
import statistics as st
from ..nlp import models, tone

def tone_label(c):
    return "Highly negative" if c >= .7 else "Negative" if c >= .5 else "Tense" if c >= .3 else "Neutral" if c >= .15 else "Positive"

def _r(d): return {k: round(v, 3) for k, v in d.items()}

def _explain(rows, i):
    """Only reports measured differences vs. the previous turn and preceding context."""
    r, out = rows[i], []
    if i:
        p = rows[i - 1]
        if r["sentiment_scores"]["negative"] - p["sentiment_scores"]["negative"] > .05:
            out.append(f"negative sentiment {p['sentiment_scores']['negative']:.0%} → {r['sentiment_scores']['negative']:.0%}")
        for k in ("anger", "frustration"):
            if r["emotions"][k] - p["emotions"][k] > .05: out.append(f"{k} probability {p['emotions'][k]:.0%} → {r['emotions'][k]:.0%}")
        out.append(f"context-smoothed conflict {p['conflict']:.0%} → {r['conflict']:.0%}")
        prev = rows[max(0, i - 3):i]
        if sum(x["conflict"] for x in prev) / len(prev) > .2: out.append("preceding turns already carried elevated conflict (disagreement context)")
    return out + r["signals"]

def analyze_conversation(msgs):
    texts = [m.text for m in msgs]
    S, E, I = models.sentiment(texts), models.emotion(texts), models.irony_base(texts)
    rows, ema, prev_neg = [], 0.0, 0.0
    for m, s, e, ir in zip(msgs, S, E, I):
        probs, sig = tone.analyze(m.text, s, ir, prev_neg)
        host, h = tone.hostility(m.text, e, s)
        raw = min(1, .35 * s["negative"] + .25 * host + .2 * (e["anger"] + e["frustration"]) + .1 * probs["passive_aggressive"] + .1 * probs["sarcasm"])
        ema = .6 * raw + .4 * ema  # earlier turns carry over: not independent messages
        prev_neg = s["negative"]
        rows.append({"turn": m.index, "speaker": m.speaker, "message": m.text, "timestamp": m.timestamp,
            "sentiment": max(s, key=s.get), "sentiment_scores": _r(s), "emotions": _r(e), "top_emotion": max(e, key=e.get),
            "toxicity": host, **probs, "tone": tone_label(ema), "conflict_raw": round(raw, 3), "conflict": round(ema, 3),
            "signals": sig + ([f"hostile terms: {', '.join(h)}"] if h else [])})
    n = len(rows)
    c = [r["conflict"] for r in rows]
    deltas = [c[0]] + [c[i] - c[i - 1] for i in range(1, n)]
    for r, d in zip(rows, deltas): r["conflict_delta"] = round(d * 100, 1)
    pk = max(range(n), key=lambda i: c[i])
    esc = round(min(1, max(0, c[pk] - min(c[:pk + 1])) / .5), 3)
    de = round((c[pk] - c[-1]) / c[pk], 3) if pk < n - 1 and c[pk] else 0
    vol = round(st.pstdev(deltas[1:]), 3) if n > 2 else 0
    order = sorted(range(1, n), key=lambda i: -deltas[i]) if n > 1 else [0]
    tp = order[0]
    triggers = [{"turn": rows[i]["turn"], "speaker": rows[i]["speaker"], "message": rows[i]["message"], "conflict_shift": rows[i]["conflict_delta"],
                 "signals": rows[i]["signals"], "explanation": _explain(rows, i)} for i in order[:3] if deltas[i] > .04]
    tot = {k: sum(r["emotions"][k] for r in rows) / n for k in models.EMOTIONS}
    dom = [k for k in sorted(tot, key=tot.get, reverse=True) if k != "neutral"][:3]
    by = {}
    for r in rows: by.setdefault(r["speaker"], []).append(r)
    spk = []
    for name, rs in by.items():
        em = {k: sum(x["emotions"][k] for x in rs) / len(rs) for k in models.EMOTIONS}
        h = max(1, len(rs) // 3)
        avg = lambda xs: sum(x["conflict"] for x in xs) / len(xs)
        spk.append({"name": name, "messages": len(rs), "avg_sentiment": round(sum(x["sentiment_scores"]["positive"] - x["sentiment_scores"]["negative"] for x in rs) / len(rs), 3),
            "model_detected_dominant_emotion": max((k for k in em if k != "neutral"), key=em.get), "avg_conflict_contribution": round(avg(rs), 3),
            "tone_trend": f"{tone_label(avg(rs[:h]))} → {tone_label(avg(rs[-h:]))}", "trajectory": [x["conflict"] for x in rs]})
    detected = esc >= .35
    return {"engine": models.engine(), "overall_tone": tone_label(sum(c) / n), "conflict_score": round(c[pk], 3), "avg_conflict": round(sum(c) / n, 3),
        "escalation_score": esc, "de_escalation_score": de, "volatility": vol, "dominant_emotions": dom,
        "escalation": {"detected": detected, "score": esc, "starting_tone": rows[0]["tone"], "current_tone": rows[-1]["tone"], "peak_turn": rows[pk]["turn"],
            "trigger": rows[tp]["message"] if detected else None, "contributing_turns": [t["turn"] for t in triggers]},
        "turning_point": {"turn": rows[tp]["turn"], "speaker": rows[tp]["speaker"], "message": rows[tp]["message"],
            "conflict_shift": rows[tp]["conflict_delta"], "explanation": _explain(rows, tp)},
        "triggers": triggers, "messages": rows, "speakers": spk,
        "timeline": [{"turn": r["turn"], "speaker": r["speaker"], "message": r["message"], "emotion": r["top_emotion"], "positive": r["sentiment_scores"]["positive"],
                      "neutral": r["sentiment_scores"]["neutral"], "negative": r["sentiment_scores"]["negative"], "conflict": r["conflict"]} for r in rows],
        "disclaimer": "Sarcasm, passive-aggression and irony values are model estimates, not facts."}
