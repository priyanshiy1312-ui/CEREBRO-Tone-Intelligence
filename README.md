# CEREBRO — Tone Intelligence (PS-01)

Conversation-level tone analysis: emotion arc, escalation, turning point, trigger messages, sarcasm / passive-aggression / irony, speaker analysis.

## Architecture
```
React+Vite+Tailwind+Recharts  ->  FastAPI (/api/analyze, /api/upload, /api/health)
  -> parser/ (WhatsApp, Slack-bracket, plain/Discord; add a Parser subclass to extend)
  -> nlp/models.py   HF models: sentiment (twitter-roberta), emotion (distilroberta), irony (twitter-roberta-irony)
  -> nlp/tone.py     sarcasm / passive-aggressive / hostility: model irony score + lexical + CONTEXT features
  -> services/context_engine.py  smoothed conflict, escalation, de-escalation, volatility, turning point, triggers
```
**Context:** each turn's conflict = 0.6·own signals + 0.4·previous smoothed conflict; positive wording after negative turns raises sarcasm/irony probability. Escalation score = (peak − lowest earlier conflict)/0.5, capped at 1; detected at ≥ 0.35. Turning point = largest single-turn conflict jump. Explanations list only measured differences vs. the previous turn.

**Honest notes:** the emotion model has no "frustration" label, so frustration is approximated from its anger/disgust mass. Sarcasm/passive-aggression use a hand-weighted feature model (no labeled sarcasm training done here) — treat as estimates. If models can't download (offline), the backend falls back to a lexicon engine and reports `engine: lexicon-fallback`; set `CEREBRO_LEXICON_ONLY=1` to force it.

## Run
```
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000        # first run downloads ~1.5 GB of models
cd frontend && npm install && npm run dev        # http://localhost:5173 (proxies /api)
```

## Demo
Click **Load Demo Conversation** (neutral → tension → frustration → conflict → peak → de-escalation). More synthetic samples: `data/demo_conversations.json`.

## Data & privacy
Synthetic data lives in `data/` and is labelled as such. For participant-sourced data, put consented exports in `data/participant/` (git-ignored) and label them in a CSV for evaluation. Uploads are processed in memory and never written to disk.

## Evaluation
`python evaluation/evaluate.py labeled.csv` (columns `text,sentiment[,emotion,sarcasm]`) prints per-class precision/recall/F1 and a sentiment confusion matrix, and sarcasm P/R/F1. **No benchmark numbers are claimed until you run it on labeled data**; dashboard output is demo prediction only. Escalation evaluation: label whole conversations as escalating/not and compare with `escalation.detected`.
