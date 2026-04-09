"""SQLite 儲存層。單檔資料庫，零維運。

兩張表：
- raw_items: 所有抓到的原始項目（含 off_topic，用於稽核）
- events:    經人工或 LLM 萃取後的事件（時間線顯示用）
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    published TEXT,
    fetched_at TEXT NOT NULL,
    relevance_score INTEGER,
    relevance_category TEXT,
    matched_keywords TEXT,
    analyzed_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    stance TEXT,
    stakeholders TEXT,
    source_urls TEXT,
    importance INTEGER DEFAULT 1,
    origin TEXT DEFAULT 'seed',
    created_at TEXT NOT NULL,
    UNIQUE(event_date, title)
);

CREATE INDEX IF NOT EXISTS idx_raw_category ON raw_items(relevance_category);
CREATE INDEX IF NOT EXISTS idx_raw_fetched ON raw_items(fetched_at);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_raw(conn: sqlite3.Connection, item, score) -> bool:
    """Insert a RawItem with its classifier score. Returns True if newly inserted."""
    try:
        conn.execute(
            """INSERT INTO raw_items
               (source, url, title, summary, published, fetched_at,
                relevance_score, relevance_category, matched_keywords)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                item.source,
                item.url,
                item.title,
                item.summary,
                item.published,
                datetime.utcnow().isoformat(),
                score.score,
                score.category,
                json.dumps(score.matched, ensure_ascii=False),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def insert_event(
    conn: sqlite3.Connection,
    event_date: str,
    title: str,
    summary: str,
    stance: str = "",
    stakeholders: list[str] | None = None,
    source_urls: list[str] | None = None,
    importance: int = 1,
    origin: str = "seed",
) -> bool:
    try:
        conn.execute(
            """INSERT INTO events
               (event_date, title, summary, stance, stakeholders,
                source_urls, importance, origin, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                event_date,
                title,
                summary,
                stance,
                json.dumps(stakeholders or [], ensure_ascii=False),
                json.dumps(source_urls or [], ensure_ascii=False),
                importance,
                origin,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def all_events(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM events ORDER BY event_date DESC, importance DESC"
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        d["stakeholders"] = json.loads(d.get("stakeholders") or "[]")
        d["source_urls"] = json.loads(d.get("source_urls") or "[]")
        out.append(d)
    return out


def top_raw_items(
    conn: sqlite3.Connection,
    limit: int = 30,
    min_category: str = "core",
    only_unanalyzed: bool = True,
) -> list[dict]:
    rank = {"off_topic": 0, "maybe": 1, "on_topic": 2, "core": 3}
    threshold = rank[min_category]
    q = "SELECT * FROM raw_items"
    if only_unanalyzed:
        q += " WHERE analyzed_at IS NULL"
    q += " ORDER BY relevance_score DESC, fetched_at DESC LIMIT ?"
    rows = conn.execute(q, (limit * 3,)).fetchall()
    return [
        dict(r)
        for r in rows
        if rank.get(r["relevance_category"], 0) >= threshold
    ][:limit]


def mark_analyzed(conn: sqlite3.Connection, raw_id: int) -> None:
    conn.execute(
        "UPDATE raw_items SET analyzed_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), raw_id),
    )
    conn.commit()


def counts(conn: sqlite3.Connection) -> dict:
    return {
        "raw_total": conn.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0],
        "raw_core": conn.execute(
            "SELECT COUNT(*) FROM raw_items WHERE relevance_category='core'"
        ).fetchone()[0],
        "raw_on_topic": conn.execute(
            "SELECT COUNT(*) FROM raw_items WHERE relevance_category='on_topic'"
        ).fetchone()[0],
        "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
    }
