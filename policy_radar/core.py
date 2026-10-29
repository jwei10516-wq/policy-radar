"""读取政策数据、打议题标签、计算业务影响，并生成简报。"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .taxonomy import ACTIONS, BUSINESS_LINES, IMPACT, ISSUES


@dataclass
class Policy:
    id: str
    title: str
    issuer: str
    level: str
    publish_date: date
    effective_date: date
    summary: str
    issues: list[str] = field(default_factory=list)
    impact: dict[str, int] = field(default_factory=dict)

    @property
    def primary_issue(self) -> str:
        """主议题：优先取标题里命中的议题。"""
        for issue in self.issues:
            if any(w in self.title for w in ISSUES[issue]):
                return issue
        return self.issues[0]

    @property
    def top_lines(self) -> list[str]:
        """影响最大的业务线（得分最高的前两个）。"""
        ranked = sorted(self.impact.items(), key=lambda kv: kv[1], reverse=True)
        return [name for name, score in ranked[:2] if score > 0]


def load_policies(path: str | Path) -> list[Policy]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    policies = [
        Policy(
            id=r["id"],
            title=r["title"],
            issuer=r["issuer"],
            level=r["level"],
            publish_date=date.fromisoformat(r["publish_date"]),
            effective_date=date.fromisoformat(r["effective_date"]),
            summary=r["summary"],
        )
        for r in rows
    ]
    for p in policies:
        p.issues = classify(p.title + p.summary)
        p.impact = score_impact(p.issues)
    return policies


def classify(text: str) -> list[str]:
    """按关键词匹配议题；一份政策可以属于多个议题。"""
    found = [issue for issue, words in ISSUES.items() if any(w in text for w in words)]
    base = "网络安全与基础制度"
    # 「互联网信息服务」常出现在各类规章标题里；已命中具体议题时，不再重复标为基础制度
    if base in found and len(found) > 1 and "网络安全" not in text:
        found.remove(base)
    return found or [base]


def score_impact(issues: list[str]) -> dict[str, int]:
    """把各议题对业务线的权重相加，得到这份政策对每条业务线的影响分。"""
    scores = {line: 0 for line in BUSINESS_LINES}
    for issue in issues:
        for line, w in IMPACT[issue].items():
            scores[line] += w
    return scores


def issue_line_matrix(policies: list[Policy]) -> dict[str, dict[str, int]]:
    """议题 × 业务线的累计影响分，用于热力图。"""
    matrix = {issue: {line: 0 for line in BUSINESS_LINES} for issue in ISSUES}
    for p in policies:
        for issue in p.issues:
            for line, w in IMPACT[issue].items():
                matrix[issue][line] += w
    return matrix


def build_brief(policies: list[Policy], today: date, lookback_days: int = 365, horizon_days: int = 180) -> str:
    """生成 Markdown 简报初稿：近期新发布、即将施行、议题分布和建议动作。"""
    recent = [p for p in policies if 0 <= (today - p.publish_date).days <= lookback_days]
    upcoming = [p for p in policies if 0 < (p.effective_date - today).days <= horizon_days]
    lines = [
        f"# 政策雷达简报（{today.isoformat()}）",
        "",
        f"> 自动生成的初稿：统计近 {lookback_days} 天发布、未来 {horizon_days} 天施行的政策。"
        "议题标签和影响分基于关键词和预设权重，正式发出前需要人工判断和改写。",
        "",
        "## 一、近期发布",
    ]
    if recent:
        lines += ["| 发布日期 | 政策 | 发布机关 | 议题 | 影响最大的业务线 |", "|---|---|---|---|---|"]
        for p in sorted(recent, key=lambda x: x.publish_date, reverse=True):
            lines.append(
                f"| {p.publish_date} | {p.title} | {p.issuer} | {'、'.join(p.issues)} | {'、'.join(p.top_lines)} |"
            )
    else:
        lines.append("本期没有新发布的政策。")

    lines += ["", "## 二、即将施行（合规日历）"]
    if upcoming:
        for p in sorted(upcoming, key=lambda x: x.effective_date):
            days = (p.effective_date - today).days
            lines.append(f"- **{p.effective_date}**（还有 {days} 天）：{p.title}，{p.summary}")
    else:
        lines.append("未来一段时间内没有即将施行的政策。")

    focus = recent + [p for p in upcoming if p not in recent]
    issue_count: dict[str, int] = {}
    for p in focus:
        for i in p.issues:
            issue_count[i] = issue_count.get(i, 0) + 1
    lines += ["", "## 三、本期议题与建议动作"]
    if issue_count:
        for issue, n in sorted(issue_count.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"- **{issue}**（{n} 份）：{ACTIONS[issue]}")
    else:
        lines.append("本期没有需要特别关注的议题。")

    lines += [
        "",
        "## 四、待人工补充",
        "- 对业务的具体影响判断（哪些产品功能、哪些团队需要调整）",
        "- 对外沟通口径：面向监管、媒体、用户各自强调什么",
        "- 需要持续跟踪的配套细则和地方执行情况",
        "",
    ]
    return "\n".join(lines)
