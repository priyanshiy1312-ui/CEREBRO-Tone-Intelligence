const j = async (r) => { if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'Request failed'); return r.json() }
export const analyze = (text) => fetch('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) }).then(j)
export const upload = (file) => { const f = new FormData(); f.append('file', file); return fetch('/api/upload', { method: 'POST', body: f }).then(j) }
export const health = () => fetch('/api/health').then(j)
