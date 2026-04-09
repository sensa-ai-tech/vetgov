"""抓取 RSS / HTML 來源。純函式，無副作用。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

import feedparser
import httpx


@dataclass
class RawItem:
    source: str
    url: str
    title: str
    summary: str
    published: str  # ISO-ish string
    tier: str = "media"  # official | media | community


def fetch_rss(
    source_name: str,
    url: str,
    tier: str = "media",
    timeout: int = 20,
) -> Iterator[RawItem]:
    """抓取 RSS/Atom feed，逐筆回傳 RawItem。"""
    try:
        resp = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "VetGovTracker/0.2 (+https://vetgov.tw)"},
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except httpx.HTTPError:
        return
        yield  # make generator

    for entry in feed.entries:
        yield RawItem(
            source=source_name,
            url=entry.get("link", "").strip(),
            title=_clean(entry.get("title", "")),
            summary=_clean(entry.get("summary", "")),
            published=entry.get("published", "")
            or entry.get("updated", "")
            or datetime.utcnow().isoformat(),
            tier=tier,
        )


def fetch_html(url: str, timeout: int = 20) -> str:
    """抓取單一 HTML 頁面，回傳純文字內容。"""
    resp = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "VetDrugTracker/0.1 (+https://github.com/)"},
    )
    resp.raise_for_status()
    return resp.text


def _clean(text: str) -> str:
    """粗略去除 HTML 標籤與多餘空白。"""
    import re

    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
