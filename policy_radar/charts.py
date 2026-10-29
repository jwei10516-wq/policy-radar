"""绘制政策时间线和「议题 × 业务线」影响热力图。"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .core import Policy, issue_line_matrix  # noqa: E402
from .taxonomy import BUSINESS_LINES, ISSUES  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

INK = "#1f2933"
MUTED = "#7b8794"
PALETTE = ["#2f6fdf", "#e0782f", "#2e9e6a", "#c6414c", "#8a63d2", "#8a8f98"]


def plot_timeline(policies: list[Policy], out: str | Path) -> None:
    """按年份和议题统计政策数量（堆叠柱状图）。"""
    years = sorted({p.publish_date.year for p in policies})
    issues = list(ISSUES)
    counts = {i: Counter() for i in issues}
    for p in policies:
        counts[p.primary_issue][p.publish_date.year] += 1

    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    bottom = [0] * len(years)
    for color, issue in zip(PALETTE, issues):
        vals = [counts[issue][y] for y in years]
        if sum(vals) == 0:
            continue
        ax.bar([str(y) for y in years], vals, bottom=bottom, color=color, label=issue, width=0.62)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_title("内容平台相关政策发布数量（按主议题）", color=INK, fontsize=12, loc="left")
    ax.set_ylabel("政策数量", color=MUTED)
    ax.tick_params(colors=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    ax.set_ylim(0, max(bottom) + 1.5)
    ax.yaxis.get_major_locator().set_params(integer=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_heatmap(policies: list[Policy], out: str | Path) -> None:
    """议题 × 业务线累计影响分。"""
    matrix = issue_line_matrix(policies)
    issues = [i for i in ISSUES if any(matrix[i].values())]
    data = [[matrix[i][line] for line in BUSINESS_LINES] for i in issues]

    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
    im = ax.imshow(data, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(BUSINESS_LINES)), BUSINESS_LINES, fontsize=9)
    ax.set_yticks(range(len(issues)), issues, fontsize=9)
    vmax = max(max(row) for row in data) or 1
    for r, row in enumerate(data):
        for c, v in enumerate(row):
            ax.text(c, r, str(v), ha="center", va="center", fontsize=8, color="white" if v > vmax * 0.55 else INK)
    ax.set_title("议题对各业务线的累计影响（政策数 × 预设权重）", color=INK, fontsize=12, loc="left")
    ax.tick_params(colors=MUTED, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
