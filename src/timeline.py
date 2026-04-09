"""把 events 匯出成靜態站吃的 JSON。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def export(
    events: list[dict],
    out_path: Path,
    sources: list[dict] | None = None,
    counts: dict | None = None,
) -> int:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "policy_effective_date": "2026-07-01",
        "events": [
            {
                "date": e.get("event_date", ""),
                "title": e.get("title", ""),
                "summary": e.get("summary", ""),
                "stance": e.get("stance", "neutral"),
                "stakeholders": e.get("stakeholders", []),
                "sources": e.get("source_urls", []),
                "importance": int(e.get("importance", 1)),
                "origin": e.get("origin", "seed"),
                "tier": e.get("tier", "media"),
            }
            for e in events
        ],
        "sources_monitored": sources or [],
        "counts": counts or {},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return len(payload["events"])
