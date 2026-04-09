"""離線關鍵字相關度分類器。零 API 成本，所有過濾都在本地完成。

分數計算：
- HIGH 關鍵字命中：+30 分
- MED 關鍵字命中：+10 分
- CONTEXT 關鍵字命中：+5 分
- 上限 100 分

分類門檻：
- core (>= 60): 核心議題，值得送 LLM 萃取
- on_topic (>= 30): 相關，保留
- maybe (>= 10): 可能相關，保留但不展示
- off_topic (< 10): 雜訊，保留於 raw_items 表但不展示
"""
from __future__ import annotations

from dataclasses import dataclass, field


# 核心法規與新制用語
KEYWORDS_HIGH = [
    "特定寵物動物用藥品",
    "指定獸醫師處方",
    "獸醫師法",
    "動物用藥品管理法",
    "處方籤",
    "防檢署",
    "動植物防疫檢疫署",
]

# 相關主題詞
KEYWORDS_MED = [
    "寵物用藥",
    "犬貓用藥",
    "心絲蟲",
    "跳蚤",
    "蜱蟲",
    "壁蝨",
    "除蚤",
    "獸醫師公會",
    "獸醫師",
    "寵物醫療",
    "動物醫院",
    "農業部",
    "寵物業者",
    "飼主",
    "寵物食品",
    "動保",
    # 第一線視角:配套缺口相關
    "電子處方",
    "跨院",
    "配套",
    "公聽會",
    "偏鄉",
    "罰則",
    "試辦",
    "過渡期",
]

# 時間點與新制描述詞
KEYWORDS_CONTEXT = [
    "7月1日",
    "7/1",
    "七月一日",
    "新制",
    "上路",
    "實施",
    "新政策",
    "新規定",
    "法規",
    "修法",
    "公告",
    "草案",
]


@dataclass
class RelevanceScore:
    score: int
    matched: list[str] = field(default_factory=list)
    category: str = "off_topic"  # core | on_topic | maybe | off_topic


def score_text(text: str) -> RelevanceScore:
    """對一段文字（通常是 title + summary）打分。"""
    if not text:
        return RelevanceScore(score=0)

    score = 0
    matched: list[str] = []

    for kw in KEYWORDS_HIGH:
        if kw in text:
            score += 30
            matched.append(kw)
    for kw in KEYWORDS_MED:
        if kw in text:
            score += 10
            matched.append(kw)
    for kw in KEYWORDS_CONTEXT:
        if kw in text:
            score += 5
            matched.append(kw)

    score = min(score, 100)

    if score >= 60:
        category = "core"
    elif score >= 30:
        category = "on_topic"
    elif score >= 10:
        category = "maybe"
    else:
        category = "off_topic"

    return RelevanceScore(score=score, matched=matched, category=category)


def is_relevant(text: str, min_category: str = "on_topic") -> bool:
    """快速檢查：text 是否達到指定相關度。"""
    rank = {"off_topic": 0, "maybe": 1, "on_topic": 2, "core": 3}
    return rank[score_text(text).category] >= rank[min_category]
