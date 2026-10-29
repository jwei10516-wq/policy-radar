import unittest
from datetime import date
from pathlib import Path

from policy_radar.core import build_brief, classify, load_policies, score_impact

DATA = Path(__file__).resolve().parent.parent / "data" / "policies.csv"


class TestCore(unittest.TestCase):
    def setUp(self):
        self.policies = load_policies(DATA)

    def test_every_policy_has_issue(self):
        self.assertTrue(all(p.issues for p in self.policies))

    def test_classify_keywords(self):
        self.assertIn("算法与人工智能", classify("生成式人工智能服务管理"))
        self.assertIn("未成年人保护", classify("未成年人网络保护条例"))

    def test_dates_are_consistent(self):
        for p in self.policies:
            self.assertLessEqual(p.publish_date, p.effective_date, p.title)

    def test_impact_scores(self):
        scores = score_impact(["算法与人工智能"])
        self.assertEqual(scores["搜索与推荐"], 3)

    def test_brief_sections(self):
        text = build_brief(self.policies, date(2025, 7, 1))
        self.assertIn("人工智能生成合成内容标识办法", text)  # 2025-09-01 施行，应出现在合规日历
        self.assertIn("## 三、本期议题与建议动作", text)


if __name__ == "__main__":
    unittest.main()
