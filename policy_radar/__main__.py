"""命令行入口。

用法：
    python -m policy_radar brief --today 2025-07-01 --out output/brief_sample.md
    python -m policy_radar charts --outdir output
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .core import build_brief, load_policies

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "policies.csv"


def main() -> None:
    parser = argparse.ArgumentParser(prog="policy_radar", description="内容平台政策追踪与议题分析")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="政策数据 CSV 路径")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("brief", help="生成 Markdown 简报初稿")
    b.add_argument("--today", default=date.today().isoformat(), help="简报日期，格式 YYYY-MM-DD")
    b.add_argument("--lookback", type=int, default=365, help="统计多少天内发布的政策")
    b.add_argument("--horizon", type=int, default=180, help="统计未来多少天内施行的政策")
    b.add_argument("--out", default="output/brief.md")

    c = sub.add_parser("charts", help="生成时间线和影响热力图")
    c.add_argument("--outdir", default="output")

    args = parser.parse_args()
    policies = load_policies(args.data)

    if args.cmd == "brief":
        text = build_brief(policies, date.fromisoformat(args.today), args.lookback, args.horizon)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"简报已生成：{args.out}")
    elif args.cmd == "charts":
        from .charts import plot_heatmap, plot_timeline

        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        plot_timeline(policies, outdir / "timeline.png")
        plot_heatmap(policies, outdir / "heatmap.png")
        print(f"图表已生成：{outdir / 'timeline.png'}，{outdir / 'heatmap.png'}")


if __name__ == "__main__":
    main()
