import React from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, AreaChart, Area, BarChart, Bar, ReferenceDot } from 'recharts'
const pct = (v) => `${Math.round(v * 100)}%`
const Tip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (<div className="max-w-xs rounded-lg border border-slate-300 bg-white p-3 text-xs shadow dark:border-slate-700 dark:bg-slate-900">
    <div className="font-semibold">Turn {d.turn} · {d.speaker}</div><div className="my-1 italic">“{d.message}”</div>
    <div>Detected emotion: <b>{d.emotion}</b></div>
    <div>Positive {pct(d.positive)} · Neutral {pct(d.neutral)} · Negative {pct(d.negative)}</div><div>Conflict intensity {pct(d.conflict)}</div></div>)
}
export function EmotionArc({ data, peak }) {
  const p = data.find((x) => x.turn === peak)
  return (<ResponsiveContainer width="100%" height={300}><LineChart data={data} margin={{ left: -10, right: 10 }}>
    <CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="turn" label={{ value: 'Turn', position: 'insideBottom', offset: -2 }} />
    <YAxis domain={[0, 1]} tickFormatter={pct} /><Tooltip content={<Tip />} /><Legend />
    <Line type="monotone" dataKey="positive" stroke="#22c55e" strokeWidth={2} dot={false} />
    <Line type="monotone" dataKey="neutral" stroke="#94a3b8" strokeWidth={2} dot={false} />
    <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} dot={false} />
    <Line type="monotone" dataKey="conflict" name="conflict intensity" stroke="#f97316" strokeWidth={3} strokeDasharray="5 3" activeDot={{ r: 6 }} />
    {p && <ReferenceDot x={p.turn} y={p.conflict} r={8} fill="#f97316" stroke="#fff" />}</LineChart></ResponsiveContainer>)
}
export const ConflictTimeline = ({ data }) => (<ResponsiveContainer width="100%" height={220}><AreaChart data={data} margin={{ left: -10 }}>
  <CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="turn" /><YAxis domain={[0, 1]} tickFormatter={pct} /><Tooltip content={<Tip />} />
  <Area type="monotone" dataKey="conflict" stroke="#f97316" fill="#f9731655" /></AreaChart></ResponsiveContainer>)
export const SpeakerCompare = ({ speakers }) => (<ResponsiveContainer width="100%" height={220}>
  <BarChart data={speakers.map((s) => ({ name: s.name, conflict: s.avg_conflict_contribution, sentiment: (s.avg_sentiment + 1) / 2 }))}>
    <CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="name" /><YAxis domain={[0, 1]} tickFormatter={pct} /><Tooltip formatter={pct} /><Legend />
    <Bar dataKey="conflict" name="avg conflict" fill="#f97316" /><Bar dataKey="sentiment" name="sentiment (0=neg, 1=pos)" fill="#22c55e" /></BarChart></ResponsiveContainer>)
