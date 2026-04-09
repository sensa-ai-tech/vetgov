"""選用的 Claude LLM 事件萃取器。沒有 API key 就自動跳過。

設計原則：
- 完全 optional。ANTHROPIC_API_KEY 沒設就回傳 None，pipeline 照常運作。
- 只對 classifier 判定為 'core' 的項目動用 LLM，避免浪費 token。
- 用 Claude Haiku 4.5（最便宜），每則 ~1K output tokens。
"""
from __future__ import annotations

import json
import os
from typing import Optional

PROMPT_TEMPLATE = """你是一個中立的政策議題追蹤分析師，專門追蹤台灣 2026/7/1 獸醫用藥新制（特定寵物動物用藥品指定獸醫師處方制度）相關發展。

請閱讀以下文章片段，產出一筆事件紀錄。只回傳 JSON，不要解釋，不要 markdown 包裝。

JSON 欄位：
{{
  "event_date": "YYYY-MM-DD",
  "title": "不超過 30 字的客觀事件標題",
  "summary": "不超過 150 字的中立摘要，只陳述事實",
  "stance": "supportive|opposed|neutral|mixed",
  "stakeholders": ["提到的主要組織或公職人員"],
  "importance": 1
}}

規則：
- stance 指的是文章主要受訪對象對新制的態度
- importance: 1=日常新聞, 2=公開發言, 3=官方公告, 4=政策轉折, 5=重大爭議或修法
- 若無法判斷日期，用 "unknown"
- 不要出現主觀形容詞（例如「嚴重」「荒謬」「可惡」）

文章：
---
標題：{title}
來源：{source}
內容：{text}
---
"""


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def analyze(
    title: str,
    source: str,
    text: str,
    model: str = "claude-haiku-4-5-20251001",
) -> Optional[dict]:
    """對單則 raw item 跑 LLM 萃取，回傳 dict 或 None。"""
    if not is_available():
        return None
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        return None

    try:
        client = Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT_TEMPLATE.format(
                        title=title or "", source=source or "", text=(text or "")[:3000]
                    ),
                }
            ],
        )
        raw = msg.content[0].text.strip()
    except Exception as e:
        print(f"[WARN] LLM call failed: {e}")
        return None

    # 容忍 ```json ... ``` 包裝
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # 基本檢核
    if not parsed.get("title") or not parsed.get("summary"):
        return None
    if parsed.get("event_date") == "unknown":
        from datetime import datetime

        parsed["event_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    parsed.setdefault("stance", "neutral")
    parsed.setdefault("stakeholders", [])
    parsed.setdefault("importance", 1)
    return parsed
