"""Sarcasm / passive-aggression / irony layer: model irony score + conversational-context features.
Outputs are probabilistic estimates from a transparent weighted feature model, not facts."""
PA = ["apparently", "whatever you say", "fine.", "if you say so", "as usual", "no worries", "thanks for nothing", "must be nice",
      "i guess", "don't worry about it", "never mind", "good for you", "per my last"]
SARC = ["of course", "oh great", "yeah right", "wow", "sure,", "totally", "brilliant", "because apparently", "how nice", "thanks a lot", "love that"]
ABS = ["never", "always", "every time", "nobody", "nothing"]
POSW = {"great", "thanks", "love", "nice", "brilliant", "perfect", "wow", "wonderful"}
HOSTILE = ["shut up", "stupid", "idiot", "hate", "useless", "pathetic", "damn", "wtf", "ridiculous", "you never", "you always", "sick of"]
import re
hits = lambda t, l: [p for p in l if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", t)]
clip = lambda x: round(max(0, min(.97, x)), 3)

def analyze(text, sent, irony_model, prev_neg):
    t = text.lower(); sm, pa, ab = hits(t, SARC), hits(t, PA), hits(t, ABS)
    pos_surface = sent["positive"] > .35 or any(w in t.split() for w in POSW)
    ctx = prev_neg > .4  # positive wording right after negative turns = incongruity
    base = irony_model if irony_model is not None else .15 + .25 * bool(sm)
    sarc = .10 + .28 * len(sm) + .35 * base + (.2 if pos_surface and ctx else 0)
    pass_ag = .08 + .26 * len(pa) + .12 * len(ab) + (.15 if ctx and sent["negative"] < .6 else 0) + (.1 if t.endswith(("...", "fine.")) else 0)
    irony = .06 + .6 * base + (.12 if pos_surface and ctx else 0)
    sig = []
    if sm: sig.append("sarcasm markers: " + ", ".join(sm))
    if pa: sig.append("passive-aggressive phrases: " + ", ".join(pa))
    if ab: sig.append("absolute language: " + ", ".join(ab))
    if pos_surface and ctx: sig.append("positive wording after negative context (possible incongruity)")
    return {"sarcasm": clip(sarc), "passive_aggressive": clip(pass_ag), "irony": clip(irony)}, sig

def hostility(text, emo, sent):
    t = text.lower(); h = hits(t, HOSTILE)
    caps = sum(1 for w in text.split() if len(w) > 2 and w.isupper())
    v = .5 * emo["anger"] + .3 * emo["frustration"] + .2 * sent["negative"] + .15 * len(h) + .05 * min(caps, 3) + .03 * min(text.count("!"), 3)
    return round(min(1, v), 3), h
