import React, { useState, useEffect } from 'react'
import { analyze, upload } from '../services/api.js'
import { DEMOS } from '../data/demo.js'
import { EmotionArc, ConflictTimeline, SpeakerCompare } from '../charts/Charts.jsx'
const pct = (v) => `${Math.round(v * 100)}%`
const Stat = ({ label, value, sub, color }) => (<div className="card"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
  <div className={`mt-1 text-2xl font-bold ${color || ''}`}>{value}</div>{sub && <div className="text-xs text-slate-500">{sub}</div>}</div>)
const Why = ({ items }) => (<ul className="mt-1 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>)
const Bar1 = ({ label, v }) => (<div className="text-xs"><div className="flex justify-between"><span>{label}</span><span>{pct(v)}</span></div>
  <div className="h-1.5 rounded bg-slate-200 dark:bg-slate-700"><div className="h-1.5 rounded bg-indigo-500" style={{ width: pct(v) }} /></div></div>)

export default function App() {
  const [text, setText] = useState(''), [res, setRes] = useState(null), [err, setErr] = useState(''), [busy, setBusy] = useState(false)
  const [dark, setDark] = useState(true)
  useEffect(() => { document.documentElement.classList.toggle('dark', dark) }, [dark])
  const run = async (fn) => { setBusy(true); setErr(''); try { setRes(await fn()) } catch (e) { setErr(e.message) } setBusy(false) }
  const loadDemo = () => { setText(DEMOS.escalating_then_deescalating); run(() => analyze(DEMOS.escalating_then_deescalating)) }
  const esc = res?.escalation
  return (<div className="mx-auto max-w-6xl space-y-4 p-4">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h1 className="text-xl font-bold">CEREBRO <span className="text-indigo-500">— Tone Intelligence</span></h1>
      <button className="rounded-lg border px-3 py-1 text-sm dark:border-slate-700" onClick={() => setDark(!dark)}>{dark ? 'Light' : 'Dark'} theme</button></header>
    <section className="card space-y-3">
      <textarea className="h-36 w-full rounded-lg border bg-transparent p-2 text-sm dark:border-slate-700" value={text} onChange={(e) => setText(e.target.value)}
        placeholder={'[10:31] Priya: I think we should change the design.\n[10:32] Rahul: Of course, because apparently my ideas are never good enough.'} />
      <div className="flex flex-wrap gap-2">
        <button disabled={busy || !text.trim()} onClick={() => run(() => analyze(text))} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">Analyze Conversation</button>
        <label className="cursor-pointer rounded-lg border px-4 py-2 text-sm dark:border-slate-700">Upload Chat (.txt)
          <input type="file" accept=".txt" hidden onChange={(e) => e.target.files[0] && run(() => upload(e.target.files[0]))} /></label>
        <button onClick={loadDemo} className="rounded-lg border px-4 py-2 text-sm dark:border-slate-700">Load Demo Conversation</button>
        {busy && <span className="self-center text-sm text-slate-500">Analyzing…</span>}</div>
      <p className="text-xs text-slate-500">🔒 Conversation data is processed for analysis and is not stored by default.</p>
      {err && <p className="text-sm text-red-500">{err}</p>}</section>
    {res && (<>
      <p className="text-xs text-slate-500">Engine: {res.engine} · Format: {res.format} · {res.disclaimer} (Demo predictions, not benchmark results.)</p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Overall tone" value={res.overall_tone} sub={`avg conflict ${pct(res.avg_conflict)}`} />
        <Stat label="Conflict score" value={pct(res.conflict_score)} sub="peak, context-smoothed" color="text-orange-500" />
        <Stat label="Escalation" value={esc.detected ? 'DETECTED' : 'Not detected'} sub={`score ${pct(res.escalation_score)} · de-escalation ${pct(res.de_escalation_score)}`} color={esc.detected ? 'text-red-500' : 'text-green-500'} />
        <Stat label="Dominant emotion" value={res.dominant_emotions[0] || 'neutral'} sub={`volatility ${res.volatility}`} /></div>
      <div className="card"><h2 className="font-semibold">Emotion Arc</h2><EmotionArc data={res.timeline} peak={esc.peak_turn} /></div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="card"><h2 className="font-semibold">Conflict Timeline</h2><ConflictTimeline data={res.timeline} /></div>
        <div className="card"><h2 className="font-semibold">Speaker Tone Comparison</h2><SpeakerCompare speakers={res.speakers} /></div></div>
      <div className="card"><h2 className="font-semibold">Conversation Escalation</h2>
        <p className={`font-bold ${esc.detected ? 'text-red-500' : 'text-green-500'}`}>{esc.detected ? 'ESCALATION DETECTED' : 'NO ESCALATION DETECTED'} ({pct(esc.score)})</p>
        <p className="text-sm">Starting tone: <b>{esc.starting_tone}</b> · Current tone: <b>{esc.current_tone}</b> · Peak conflict: <b>Turn {esc.peak_turn}</b></p>
        {esc.trigger && <p className="text-sm">Main trigger: “{esc.trigger}”</p>}
        <p className="text-sm">Contributing turns: {esc.contributing_turns.join(', ') || '—'}</p></div>
      <div className="card"><h2 className="font-semibold">Turning Point — Turn {res.turning_point.turn} ({res.turning_point.speaker})</h2>
        <p className="text-sm italic">“{res.turning_point.message}”</p><p className="text-sm">Conflict shift: +{res.turning_point.conflict_shift}</p>
        <p className="mt-1 text-sm">Why (measured signals):</p><Why items={res.turning_point.explanation} /></div>
      <div className="card"><h2 className="font-semibold">Trigger Messages</h2>
        {res.triggers.map((t) => (<div key={t.turn} className="mt-2 rounded-lg border p-2 text-sm dark:border-slate-700">
          <b>Turn {t.turn} · {t.speaker}</b> — +{t.conflict_shift} conflict<div className="italic">“{t.message}”</div><Why items={t.explanation} /></div>))}</div>
      <div className="card"><h2 className="font-semibold">Speaker Analysis</h2><div className="mt-2 grid gap-3 md:grid-cols-2">
        {res.speakers.map((s) => (<div key={s.name} className="rounded-lg border p-3 text-sm dark:border-slate-700"><b>{s.name}</b>
          <div>Messages: {s.messages}</div><div>Model-detected dominant emotion: {s.model_detected_dominant_emotion}</div>
          <div>Avg conflict contribution: {pct(s.avg_conflict_contribution)}</div><div>Tone trend: {s.tone_trend}</div></div>))}</div></div>
      <div className="card"><h2 className="font-semibold">Message-level Analysis</h2>
        <p className="text-xs text-slate-500">Sarcasm, passive-aggressive and irony values are model predictions, not facts.</p>
        <div className="mt-2 space-y-2">{res.messages.map((m) => (<details key={m.turn} className="rounded-lg border p-2 text-sm dark:border-slate-700">
          <summary className="cursor-pointer"><b>#{m.turn} {m.speaker}</b>: {m.message} <span className="ml-1 rounded bg-slate-200 px-1.5 text-xs dark:bg-slate-700">{m.tone} · {m.top_emotion}</span></summary>
          <div className="mt-2 grid gap-2 sm:grid-cols-3"><Bar1 label="Sarcasm" v={m.sarcasm} /><Bar1 label="Passive-aggressive" v={m.passive_aggressive} /><Bar1 label="Irony" v={m.irony} />
            <Bar1 label="Toxicity / hostility" v={m.toxicity} /><Bar1 label="Negative sentiment" v={m.sentiment_scores.negative} /><Bar1 label="Conflict (context)" v={m.conflict} /></div>
          {m.signals.length > 0 && <Why items={m.signals} />}</details>))}</div></div></>)}
  </div>)
}
