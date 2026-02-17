#!/usr/bin/env python3
"""
Inventory script for volume descriptives.

Reads data/reddit_comments_replies_review.json and writes a markdown summary to
outputs/analysis/inventory_summary.md.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


METRICS = ("neg", "neu", "pos", "compound", "score")


@dataclass
class Stats:
    n: int
    mean: Optional[float]
    median: Optional[float]
    stdev: Optional[float]
    min_val: Optional[float]
    max_val: Optional[float]


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _compute_stats(values: Iterable[Optional[float]]) -> Stats:
    cleaned = [v for v in values if v is not None]
    if not cleaned:
        return Stats(0, None, None, None, None, None)
    n = len(cleaned)
    mean = statistics.mean(cleaned)
    median = statistics.median(cleaned)
    stdev = statistics.stdev(cleaned) if n > 1 else 0.0
    return Stats(n, mean, median, stdev, min(cleaned), max(cleaned))


def _stats_table(metrics_stats: dict[str, Stats]) -> str:
    header = "| Metric | Mean | Median | Std Dev | Min | Max | n |\n|---|---|---|---|---|---|---|\n"
    rows = []
    for metric, stats in metrics_stats.items():
        if stats.n == 0:
            rows.append(f"| {metric} | — | — | — | — | — | 0 |")
            continue
        rows.append(
            "| {metric} | {mean:.4f} | {median:.4f} | {stdev:.4f} | {min_val:.4f} | {max_val:.4f} | {n} |".format(
                metric=metric,
                mean=stats.mean,
                median=stats.median,
                stdev=stats.stdev,
                min_val=stats.min_val,
                max_val=stats.max_val,
                n=stats.n,
            )
        )
    return header + "\n".join(rows) + "\n"


def _is_not_relevant(item: dict) -> bool:
    if item.get("not_relevant") is True:
        return True
    if item.get("exclude") is True:
        reason = (item.get("exclude_reason") or "").lower()
        if "not hll" in reason or "non-hll" in reason:
            return False
        return True
    return False


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "reddit_comments_replies_review.json"
    output_dir = project_root / "outputs" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "inventory_summary.md"

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if not _is_not_relevant(item)]

    posts = [item for item in data if item.get("type") == "post"]
    hll_posts = [item for item in posts if item.get("hll") is True]

    hll_comments_replies = [
        item
        for item in data
        if item.get("type") in ("comment", "reply")
        and item.get("hll") is True
        and item.get("is_op") is False
    ]

    non_hll_comments_replies = [
        item
        for item in data
        if item.get("type") in ("comment", "reply")
        and item.get("non_hll") is True
    ]

    def stats_for_items(items):
        metrics_stats = {}
        for metric in METRICS:
            metrics_stats[metric] = _compute_stats(_to_float(i.get(metric)) for i in items)
        return metrics_stats

    hll_post_stats = stats_for_items(hll_posts)
    hll_comment_reply_stats = stats_for_items(hll_comments_replies)
    non_hll_comment_reply_stats = stats_for_items(non_hll_comments_replies)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# Inventory Summary\n")
    lines.append(f"- Source: `{data_path}`\n")
    lines.append(f"- Generated: {now}\n")
    lines.append("## How To Read This Summary\n")
    lines.append("### Slices\n")
    lines.append("- Slice A: Posts by evident HLLs (`type=post`, `hll=true`).\n")
    lines.append(
        "- Slice B: Comments/replies by evident HLLs excluding OP replies (`type in {comment, reply}`, `hll=true`, `is_op=false`).\n"
    )
    lines.append(
        "- Slice C: Comments/replies by non‑HLLs (`type in {comment, reply}`, `non_hll=true`).\n"
    )
    lines.append("- Slice Z: Entire dataset (excluding N/R).\n")
    lines.append("### Variables\n")
    lines.append(
        "- `neg`, `neu`, `pos`: VADER sentiment proportions for negative, neutral, and positive tone (0–1).\n"
    )
    lines.append(
        "- `compound`: VADER composite sentiment score (−1 to 1), where higher is more positive overall.\n"
    )
    lines.append("- `score`: Reddit score (upvotes minus downvotes).\n")

    lines.append("## Slice A: Posts by evident HLLs\n")
    lines.append(f"Count of posts: {len(hll_posts)}\n")
    lines.append(_stats_table(hll_post_stats))

    lines.append("## Slice B: Comments/Replies by evident HLLs (excluding OP replies)\n")
    lines.append(f"Count of comments/replies: {len(hll_comments_replies)}\n")
    lines.append(_stats_table(hll_comment_reply_stats))

    lines.append("## Slice C: Comments/Replies by non-HLLs\n")
    lines.append(f"Count of comments/replies: {len(non_hll_comments_replies)}\n")
    lines.append(_stats_table(non_hll_comment_reply_stats))

    lines.append("## Slice Z: Entire Dataset (excluding N/R)\n")
    lines.append(f"Count of items: {len(data)}\n")
    lines.append(_stats_table(stats_for_items(data)))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote inventory summary to: {output_path}")


if __name__ == "__main__":
    main()
