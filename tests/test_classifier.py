"""Classifier 單元測試 — 保證關鍵字過濾的基本行為。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.classifier import score_text, is_relevant  # noqa: E402


class TestClassifier(unittest.TestCase):
    def test_core_keywords_hit(self):
        text = "農業部公告：特定寵物動物用藥品指定獸醫師處方制度將於 7 月 1 日上路"
        score = score_text(text)
        self.assertEqual(score.category, "core")
        self.assertGreaterEqual(score.score, 60)
        self.assertIn("特定寵物動物用藥品", score.matched)

    def test_off_topic(self):
        text = "今日股市收盤大漲，台積電再創新高"
        score = score_text(text)
        self.assertEqual(score.category, "off_topic")
        self.assertEqual(score.matched, [])

    def test_on_topic_medium(self):
        text = "獸醫師公會對於寵物醫療政策提出建議"
        score = score_text(text)
        self.assertIn(score.category, ("on_topic", "maybe"))
        self.assertTrue(any(kw in score.matched for kw in ("獸醫師公會", "寵物醫療")))

    def test_empty_text(self):
        score = score_text("")
        self.assertEqual(score.score, 0)
        self.assertEqual(score.category, "off_topic")

    def test_score_cap(self):
        text = (
            "特定寵物動物用藥品 指定獸醫師處方 獸醫師法 動物用藥品管理法 "
            "處方籤 防檢署 動植物防疫檢疫署 寵物用藥"
        )
        score = score_text(text)
        self.assertEqual(score.score, 100)

    def test_is_relevant_helper(self):
        self.assertTrue(is_relevant("農業部公告處方籤新制", "on_topic"))
        self.assertFalse(is_relevant("天氣晴", "on_topic"))


if __name__ == "__main__":
    unittest.main()
