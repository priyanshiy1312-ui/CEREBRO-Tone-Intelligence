"""Pluggable chat parsers. Add a Parser subclass and register it in PARSERS for Slack/Discord exports."""
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Msg:
    index: int
    speaker: str
    text: str
    timestamp: Optional[str] = None

class Parser:
    name = "base"
    rx = None
    def match(self, line):
        m = self.rx.match(line)
        return (m.group("t") if "t" in self.rx.groupindex else None, m.group("s"), m.group("m")) if m else None

class WhatsApp(Parser):  # 12/03/24, 10:31 - Priya: hi  |  [12/03/24, 10:31:02] Priya: hi
    name = "whatsapp"
    rx = re.compile(r"^\[?(?P<t>\d{1,2}[/.]\d{1,2}[/.]\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s*[-–]?\s*(?P<s>[^:]{1,40}):\s*(?P<m>.*)$")

class Bracket(Parser):   # [10:31] Priya: hi  (Slack-style export)
    name = "slack-bracket"
    rx = re.compile(r"^\[(?P<t>[^\]]+)\]\s*(?P<s>[^:]{1,40}):\s*(?P<m>.*)$")

class Plain(Parser):     # Priya: hi  (Discord copy-paste / generic)
    name = "plain"
    rx = re.compile(r"^(?P<s>[A-Za-z][\w .'-]{0,30}):\s+(?P<m>.+)$")

PARSERS = [WhatsApp(), Bracket(), Plain()]

def parse_chat(raw: str):
    msgs, fmt = [], None
    for line in raw.replace("\u200e", "").splitlines():
        line = line.strip()
        if not line: continue
        hit = next(((p, p.match(line)) for p in PARSERS if p.match(line)), None)
        if hit:
            p, (t, s, m) = hit
            fmt = fmt or p.name
            if m.lower().startswith("<media omitted"): continue
            msgs.append(Msg(len(msgs) + 1, s.strip(), m.strip(), t))
        elif msgs:
            msgs[-1].text += " " + line
    return msgs, fmt or "unknown"
