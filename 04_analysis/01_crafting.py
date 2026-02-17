#!/usr/bin/env python3
"""
Crafting script for additional variables described in docs/analysis.md.

Calculates statistics for comments/replies generated per post (excluding OP replies)
and writes a markdown summary to outputs/analysis/crafting_summary.md.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional


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


def _root_post_id(item, id_map) -> Optional[str]:
    parent = item.get("parent_id") or ""
    seen = set()
    while parent:
        if parent.startswith("t3_"):
            return parent[3:]
        if parent.startswith("t1_"):
            parent_id = parent[3:]
            if parent_id in seen:
                break
            seen.add(parent_id)
            parent_item = id_map.get(parent_id)
            if not parent_item:
                break
            parent = parent_item.get("parent_id") or ""
            continue
        break
    return None


def _stats_table(stats: Stats) -> str:
    header = "| Metric | Mean | Median | Std Dev | Min | Max | n |\n|---|---|---|---|---|---|---|\n"
    if stats.n == 0:
        return header + "| count_per_post | — | — | — | — | — | 0 |\n"
    return (
        header
        + "| count_per_post | {mean:.4f} | {median:.4f} | {stdev:.4f} | {min_val:.4f} | {max_val:.4f} | {n} |\n".format(
            mean=stats.mean,
            median=stats.median,
            stdev=stats.stdev,
            min_val=stats.min_val,
            max_val=stats.max_val,
            n=stats.n,
        )
    )


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
    posts_path = project_root / "data" / "posts.json"
    output_dir = project_root / "outputs" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "crafting_summary.md"
    chart_ehll_vs_nonehll = output_dir / "comments_replies_ehll_vs_nonehll.png"
    chart_cross_posting = output_dir / "cross_posting_histogram.png"
    chart_timeline = output_dir / "timeline_posts_absolute.png"
    chart_timeline_relative = output_dir / "timeline_posts_relative.png"
    chart_timeline_relative_rotated = output_dir / "timeline_posts_relative_rotated.png"
    chart_timeline_relative_channels = output_dir / "timeline_posts_relative_channels.png"
    chart_timeline_relative_subreddit = output_dir / "timeline_posts_relative_subreddit.png"

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if not _is_not_relevant(item)]

    posts_data = {}
    if posts_path.exists():
        with posts_path.open("r", encoding="utf-8") as f:
            posts_data = json.load(f)

    id_map = {item.get("id"): item for item in data if item.get("id")}

    posts = [item for item in data if item.get("type") == "post"]

    root_post_by_item = {}
    for item in data:
        if item.get("type") in ("comment", "reply"):
            root_post_by_item[item.get("id")] = _root_post_id(item, id_map)

    counts_per_post = []
    for post in posts:
        post_id = post.get("id")
        count = 0
        for item in data:
            if item.get("type") not in ("comment", "reply"):
                continue
            if item.get("is_op") is True:
                continue
            root_post = root_post_by_item.get(item.get("id"))
            if root_post == post_id:
                count += 1
        counts_per_post.append(count)

    counts_stats = _compute_stats(_to_float(v) for v in counts_per_post)

    # Subreddit activity summary
    post_id_to_subreddit = {}
    posts_per_subreddit = {}
    for subreddit, items in posts_data.items():
        for item in items:
            post_id = item.get("id")
            if post_id:
                post_id_to_subreddit[post_id] = subreddit

    for post in posts:
        post_id = post.get("id")
        if not post_id:
            continue
        subreddit = post_id_to_subreddit.get(post_id)
        if not subreddit:
            continue
        posts_per_subreddit[subreddit] = posts_per_subreddit.get(subreddit, 0) + 1

    hll_posts_per_subreddit = {}
    hll_scores_per_subreddit = {}
    for post in posts:
        post_id = post.get("id")
        if not post_id:
            continue
        subreddit = post_id_to_subreddit.get(post_id)
        if not subreddit:
            continue
        if post.get("hll") is True:
            hll_posts_per_subreddit[subreddit] = hll_posts_per_subreddit.get(subreddit, 0) + 1
            score_val = _to_float(post.get("score"))
            if score_val is not None:
                hll_scores_per_subreddit.setdefault(subreddit, []).append(score_val)

    comment_reply_counts_per_post = {}
    for item in data:
        if item.get("type") not in ("comment", "reply"):
            continue
        if item.get("is_op") is True:
            continue
        root_post = root_post_by_item.get(item.get("id"))
        if not root_post:
            continue
        comment_reply_counts_per_post[root_post] = comment_reply_counts_per_post.get(root_post, 0) + 1

    avg_comments_per_subreddit = {}
    for post_id, count in comment_reply_counts_per_post.items():
        subreddit = post_id_to_subreddit.get(post_id)
        if not subreddit:
            continue
        avg_comments_per_subreddit.setdefault(subreddit, []).append(count)

    # Visualization: proportion of comments/replies that are eHLL vs non-HLL
    comments_replies = [
        item for item in data if item.get("type") in ("comment", "reply")
    ]
    ehll_count = sum(1 for item in comments_replies if item.get("hll") is True)
    nonehll_count = sum(1 for item in comments_replies if item.get("non_hll") is True)
    total_cr = ehll_count + nonehll_count

    # Cross-posting analysis: how often eHLL authors comment/reply across posts
    post_by_id = {post.get("id"): post for post in posts if post.get("id")}
    root_post_by_item = {}
    for item in data:
        if item.get("type") in ("comment", "reply"):
            root_post_by_item[item.get("id")] = _root_post_id(item, id_map)

    ehll_author_posts = {}
    for item in data:
        if item.get("type") not in ("comment", "reply"):
            continue
        if item.get("hll") is not True:
            continue
        if item.get("is_op") is True:
            continue
        author = (item.get("author") or "").strip()
        if not author:
            continue
        root_post = root_post_by_item.get(item.get("id"))
        if not root_post:
            continue
        ehll_author_posts.setdefault(author, set()).add(root_post)

    ehll_post_counts = {a: len(pids) for a, pids in ehll_author_posts.items()}
    cross_post_authors = {a: c for a, c in ehll_post_counts.items() if c > 1}

    # Write markdown summary
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# Crafting Summary\n")
    lines.append(f"- Source: `{data_path}`\n")
    lines.append(f"- Generated: {now}\n")
    lines.append("## Comments/Replies per Post (excluding OP replies)\n")
    lines.append(f"Number of posts: {len(posts)}\n")
    lines.append(_stats_table(counts_stats))
    lines.append("## Subreddit Activity Summary\n")
    lines.append("| Subreddit | HLL Posts | All Posts | Avg Score (HLL Posts) | Avg Comments/Replies per Post |\n|---|---|---|---|---|\n")
    for subreddit in sorted(posts_per_subreddit.keys()):
        hll_count = hll_posts_per_subreddit.get(subreddit, 0)
        all_count = posts_per_subreddit.get(subreddit, 0)
        if hll_scores_per_subreddit.get(subreddit):
            avg_score = sum(hll_scores_per_subreddit[subreddit]) / len(hll_scores_per_subreddit[subreddit])
            avg_score_str = f"{avg_score:.2f}"
        else:
            avg_score_str = "—"
        if avg_comments_per_subreddit.get(subreddit):
            avg_comments = sum(avg_comments_per_subreddit[subreddit]) / len(avg_comments_per_subreddit[subreddit])
            avg_comments_str = f"{avg_comments:.2f}"
        else:
            avg_comments_str = "—"
        lines.append(f"| {subreddit} | {hll_count} | {all_count} | {avg_score_str} | {avg_comments_str} |")
    lines.append("")
    lines.append("## Visuals\n")
    lines.append("### Comments/Replies: eHLL vs Non-HLL\n")
    lines.append(f"- File: `{chart_ehll_vs_nonehll}`\n")
    lines.append("- Description: Percent of total comments/replies authored by eHLL vs Non‑HLL.\n")
    lines.append("- Notes: Based on comment/reply counts (not unique authors).\n")

    lines.append("### Cross‑Posting by eHLL Authors\n")
    lines.append(f"- File: `{chart_cross_posting}`\n")
    lines.append("- Description: Histogram of the number of distinct posts each eHLL author commented/replied to.\n")
    lines.append("- Notes: Comments/replies only; excludes OP replies.\n")

    lines.append("### Timeline (Absolute)\n")
    lines.append(f"- File: `{chart_timeline}`\n")
    lines.append("- Description: Posts only over absolute time (UTC), y‑axis = post author [language].\n")
    lines.append("- Notes: Uses jitter to reduce overlap.\n")

    lines.append("### Timeline (Relative)\n")
    lines.append(f"- File: `{chart_timeline_relative}`\n")
    lines.append("- Description: Posts/comments/replies over hours since post, y‑axis = post author [language].\n")
    lines.append("- Notes: Top 10 posts by total comments/replies; shapes denote type (post/comment/reply); colors denote HLL vs Non‑HLL.\n")
    lines.append("### Timeline (Relative, Rotated Waterfall)\n")
    lines.append(f"- File: `{chart_timeline_relative_rotated}`\n")
    lines.append("- Description: Same data as relative timeline, rotated (x = post order by date, y = hours since post), ordered by post date.\n")
    lines.append("- Notes: Top 10 posts by total comments/replies; no jitter; drops points > 150 hours; time increases downward; bottom labels = author; years grouped with subtle separators; channels separated left-to-right (post/comment/reply).\n")
    lines.append("### Timeline (Relative, Channelized)\n")
    lines.append(f"- File: `{chart_timeline_relative_channels}`\n")
    lines.append("- Description: Same data as relative timeline with separate lanes for post/comment/reply.\n")
    lines.append("- Notes: Top 10 posts by total comments/replies; no jitter; extra spacing between posts and lanes.\n")
    lines.append("### Timeline (Relative, All Posts by Subreddit)\n")
    lines.append(f"- File: `{chart_timeline_relative_subreddit}`\n")
    lines.append("- Description: All posts/comments/replies; colors indicate subreddit, shapes indicate type.\n")
    lines.append("- Notes: Points > 150 hours not shown.\n")

    # Cross-posting histogram + summary table
    lines.append("## Cross-posting by eHLL Authors (Comments/Replies Only)\n")
    lines.append(
        "- Definition: for each eHLL author, count how many different posts they commented/replied to (excluding OP replies).\n"
    )
    if not ehll_post_counts:
        lines.append("No eHLL comments/replies found.\n")
    else:
        lines.append("### eHLL Authors and Posts Participated In\n")
        lines.append("| eHLL Author | # of Posts Commented/Replied To | Post IDs |\n|---|---|---|")
        one_post_authors = [a for a, c in ehll_post_counts.items() if c == 1]
        for author in sorted(ehll_post_counts, key=lambda a: (-ehll_post_counts[a], a)):
            if ehll_post_counts[author] == 1:
                continue
            post_ids = sorted(ehll_author_posts[author])
            lines.append(f"| {author} | {ehll_post_counts[author]} | {', '.join(post_ids)} |")
        if one_post_authors:
            lines.append(f"| Other (1 post) | {len(one_post_authors)} | — |")
        lines.append("")

    # Generate charts (matplotlib)
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for chart generation. Install it and re-run."
        ) from exc

    # Bar chart: HLL vs Non-HLL proportions
    if total_cr == 0:
        labels = ["HLL", "Non-HLL"]
        values = [0, 0]
    else:
        labels = ["HLL", "Non-HLL"]
        values = [ehll_count / total_cr * 100, nonehll_count / total_cr * 100]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(labels, values, color=["#2c7fb8", "#fdbb84"])
    plt.title("Comments/Replies: HLL vs Non-HLL (%)")
    plt.figtext(
        0.5,
        -0.02,
        "Note: percentages are based on comment/reply counts (not unique authors).",
        ha="center",
        fontsize=8,
    )
    plt.ylabel("Percent")
    plt.ylim(0, 100)
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.1f}%",
            ha="center",
        )
    plt.tight_layout()
    plt.savefig(chart_ehll_vs_nonehll, dpi=200)
    plt.close()

    # Histogram
    if ehll_post_counts:
        freq = {}
        for count in ehll_post_counts.values():
            freq[count] = freq.get(count, 0) + 1
        plt.figure(figsize=(6, 4))
        x_vals = sorted(freq.keys())
        y_vals = [freq[x] for x in x_vals]
        plt.bar([str(x) for x in x_vals], y_vals, color="#2c7fb8")
        plt.title("eHLL Authors: # of Posts Participated In")
        plt.xlabel("Distinct Posts (comments/replies only)")
        plt.ylabel("# of eHLL Authors")
        plt.tight_layout()
        plt.savefig(chart_cross_posting, dpi=200)
        plt.close()

    # Timeline visualization
    post_ids = [p.get("id") for p in posts if p.get("id")]
    post_index = {pid: idx for idx, pid in enumerate(post_ids)}
    post_author = {
        p.get("id"): (p.get("author") or "[deleted]")
        for p in posts
        if p.get("id")
    }
    post_language = {
        p.get("id"): (p.get("language") or "Unknown")
        for p in posts
        if p.get("id")
    }
    post_created = {
        p.get("id"): p.get("created_utc")
        for p in posts
        if p.get("id") and p.get("created_utc") is not None
    }

    def _label_for_post(post_id: str) -> str:
        author = post_author.get(post_id, "[deleted]")
        language = post_language.get(post_id, "Unknown")
        return f"{author} [{language}]"

    def _color_for_item(item: dict) -> str:
        if item.get("hll") is True:
            return "#1e88e5"  # HLL - blue
        if item.get("non_hll") is True:
            return "#e53935"  # Non-HLL - red
        return "#9e9e9e"

    def _y_for_post(post_id: str, jitter: float = 0.0) -> float:
        return float(post_index.get(post_id, 0)) + jitter

    timeline_points = []
    for item in data:
        created = item.get("created_utc")
        if created is None:
            continue
        if item.get("type") == "post":
            root_post = item.get("id")
        else:
            root_post = root_post_by_item.get(item.get("id"))
        if not root_post:
            continue
        timeline_points.append((created, item.get("type"), root_post, item.get("id")))

    if timeline_points and post_ids:
        import random
        import matplotlib.dates as mdates

        rng = random.Random(0)

        def _jitter():
            return rng.uniform(-0.08, 0.08)

        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        for created, item_type, root_post, item_id in timeline_points:
            if item_type != "post":
                continue
            item_obj = id_map.get(item_id) or {}
            color = _color_for_item(item_obj)
            marker = "s"  # post
            size = 120
            ax.scatter(
                datetime.fromtimestamp(created, tz=timezone.utc),
                _y_for_post(root_post, _jitter()),
                c=[color],
                marker=marker,
                s=size,
                alpha=0.8,
                edgecolors="black",
                linewidths=0.4,
            )

        ax.set_title("Timeline (Absolute Time) by Post")
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("Post Author")
        ax.set_yticks(range(len(post_ids)))
        ax.set_yticklabels([_label_for_post(pid) for pid in post_ids])
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=30, ha="right")

        plt.tight_layout()
        plt.savefig(chart_timeline, dpi=200)
        plt.close()

        # Relative overlay timeline (hours since post, posts on y-axis)
        rel_points = []
        for created, item_type, root_post, item_id in timeline_points:
            post_time = post_created.get(root_post)
            if post_time is None:
                continue
            delta_hours = (created - post_time) / 3600.0
            rel_points.append((delta_hours, item_type, root_post, item_id))

        if rel_points:
            plt.figure(figsize=(10, 5))
            ax = plt.gca()
            max_hours = 800
            # Top 10 posts by total comment/reply volume
            top_posts = sorted(
                comment_reply_counts_per_post.items(),
                key=lambda kv: kv[1],
                reverse=True,
            )[:10]
            rel_post_ids = [pid for pid, _count in top_posts]
            rel_post_index = {pid: idx for idx, pid in enumerate(rel_post_ids)}

            base_points = [p for p in rel_points if p[2] in rel_post_index]
            filtered_points = [p for p in base_points if p[0] <= max_hours]
            dropped_points = len(base_points) - len(filtered_points)

            post_spacing = 1.8
            channel_spacing = 0.3

            def _y_for_post_rel(post_id: str, jitter: float = 0.0) -> float:
                return float(rel_post_index.get(post_id, 0)) + jitter

            max_hours_rotated = 150
            rotated_points = [p for p in filtered_points if p[0] <= max_hours_rotated]
            rotated_dropped = len(filtered_points) - len(rotated_points)
            for delta_hours, item_type, root_post, item_id in rotated_points:
                item_obj = id_map.get(item_id) or {}
                color = _color_for_item(item_obj)
                if item_type == "post":
                    marker = "s"
                    size = 120
                elif item_type == "comment":
                    marker = "o"
                    size = 50
                else:
                    marker = "^"
                    size = 40
                ax.scatter(
                    delta_hours,
                    _y_for_post_rel(root_post, _jitter()),
                    c=[color],
                    marker=marker,
                    s=size,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=0.4,
                )
            ax.set_title("Relative Timeline by Post")
            ax.set_xlabel("Hours Since Post (UTC)")
            ax.set_ylabel("Post Author")
            ax.set_yticks(range(len(rel_post_ids)))
            ax.set_yticklabels([_label_for_post(pid) for pid in rel_post_ids])
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            # Legend for shapes and colors
            shape_handles = [
                plt.Line2D([0], [0], marker="s", color="w", markerfacecolor="#444", markeredgecolor="black", markersize=7, label="Post"),
                plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#444", markeredgecolor="black", markersize=7, label="Comment"),
                plt.Line2D([0], [0], marker="^", color="w", markerfacecolor="#444", markeredgecolor="black", markersize=7, label="Reply"),
            ]
            color_handles = [
                plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#1e88e5", markeredgecolor="black", markersize=7, label="HLL"),
                plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#e53935", markeredgecolor="black", markersize=7, label="Non-HLL"),
            ]
            ax.legend(handles=shape_handles + color_handles, title="Legend", bbox_to_anchor=(1.02, 1), loc="upper left")
            plt.tight_layout()
            plt.savefig(chart_timeline_relative, dpi=200)
            plt.close()

            # Rotated waterfall (time on y-axis, posts on x-axis), ordered by post date
            plt.figure(figsize=(9, 9))
            ax = plt.gca()
            rel_post_ids_by_date = sorted(
                rel_post_ids,
                key=lambda pid: post_created.get(pid, 0),
            )
            rel_post_index_by_date = {pid: idx for idx, pid in enumerate(rel_post_ids_by_date)}
            post_years = {}
            for pid in rel_post_ids_by_date:
                ts = post_created.get(pid)
                if ts:
                    post_years[pid] = datetime.fromtimestamp(ts, tz=timezone.utc).year
            channel_offsets = {
                "post": -channel_spacing,
                "comment": 0.0,
                "reply": channel_spacing,
            }
            for delta_hours, item_type, root_post, item_id in filtered_points:
                item_obj = id_map.get(item_id) or {}
                color = _color_for_item(item_obj)
                if item_type == "post":
                    marker = "s"
                    size = 120
                elif item_type == "comment":
                    marker = "o"
                    size = 50
                else:
                    marker = "^"
                    size = 40
                base_x = rel_post_index_by_date.get(root_post, 0) * post_spacing
                ax.scatter(
                    base_x + channel_offsets.get(item_type, 0.0),
                    delta_hours,
                    c=[color],
                    marker=marker,
                    s=size,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=0.4,
                )
            ax.set_title("Top 10 Upvoted HLL-Generated Posts (2021–2026) and Activity in the Hours After Posting")
            ax.set_xlabel("Post Author")
            ax.set_ylabel("Hours Since Post (UTC)")
            tick_positions = [rel_post_index_by_date[pid] * post_spacing for pid in rel_post_ids_by_date]
            tick_labels = []
            for pid in rel_post_ids_by_date:
                post_item = id_map.get(pid, {})
                language = post_item.get("language") or "Unknown"
                tick_labels.append(f"{pid}\n[{language}]")
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=0, ha="center", fontsize=7)
            ax.xaxis.set_label_position("bottom")
            ax.xaxis.tick_bottom()
            ax.invert_yaxis()
            y_pad = max_hours_rotated * 0.05
            ax.set_ylim(max_hours_rotated + y_pad, -y_pad)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.legend(handles=shape_handles + color_handles, title="Legend", bbox_to_anchor=(1.02, 1), loc="upper left")
            ax.text(
                1.02,
                0.72,
                f"{rotated_dropped} points > {max_hours_rotated} hours not shown",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                color="#555555",
            )

            # Subtle year separators (grouped by post year)
            if post_years:
                year_groups = {}
                for pid in rel_post_ids_by_date:
                    year = post_years.get(pid)
                    if year is None:
                        continue
                    year_groups.setdefault(year, []).append(pid)
                years_sorted = sorted(year_groups.keys())
                for year in years_sorted:
                    group = year_groups[year]
                    start_idx = rel_post_index_by_date[group[0]]
                    end_idx = rel_post_index_by_date[group[-1]]
                    mid_x = (start_idx + end_idx) / 2 * post_spacing
                    ax.text(
                        mid_x,
                        140,
                        str(year),
                        ha="center",
                        va="center",
                        color="#333333",
                        fontsize=16,
                        bbox=dict(facecolor="white", edgecolor="#999999", boxstyle="round,pad=0.3", alpha=0.9),
                    )
                # draw separating lines between years
                for year in years_sorted[:-1]:
                    group = year_groups[year]
                    last_idx = rel_post_index_by_date[group[-1]]
                    line_x = (last_idx + 0.5) * post_spacing
                    ax.axvline(line_x, color="#cccccc", linestyle="--", linewidth=1, alpha=0.7)
            plt.tight_layout()
            plt.savefig(chart_timeline_relative_rotated, dpi=300)
            plt.close()

            # Relative timeline for all posts, colored by subreddit
            try:
                import matplotlib.cm as cm
            except ImportError:
                cm = None

            all_post_ids = sorted(post_created.keys(), key=lambda pid: post_created.get(pid, 0))
            all_post_index = {pid: idx for idx, pid in enumerate(all_post_ids)}
            all_points = [p for p in rel_points if p[2] in all_post_index]
            max_hours_sub = 150
            sub_points = [p for p in all_points if p[0] <= max_hours_sub]
            sub_dropped = len(all_points) - len(sub_points)

            subreddits = sorted(
                {post_id_to_subreddit.get(pid, "Unknown") for pid in all_post_ids}
            )
            color_map = {}
            if cm:
                palette = cm.get_cmap("tab20", max(1, len(subreddits)))
                for idx, sub in enumerate(subreddits):
                    color_map[sub] = palette(idx)
            else:
                for sub in subreddits:
                    color_map[sub] = "#999999"

            plt.figure(figsize=(9, 9))
            ax = plt.gca()
            channel_offsets = {
                "post": -channel_spacing,
                "comment": 0.0,
                "reply": channel_spacing,
            }
            for delta_hours, item_type, root_post, item_id in sub_points:
                sub = post_id_to_subreddit.get(root_post, "Unknown")
                color = color_map.get(sub, "#999999")
                if item_type == "post":
                    marker = "s"
                    size = 120
                elif item_type == "comment":
                    marker = "o"
                    size = 50
                else:
                    marker = "^"
                    size = 40
                base_x = all_post_index.get(root_post, 0) * post_spacing
                ax.scatter(
                    base_x + channel_offsets.get(item_type, 0.0),
                    delta_hours,
                    c=[color],
                    marker=marker,
                    s=size,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=0.4,
                )

            tick_positions = [all_post_index[pid] * post_spacing for pid in all_post_ids]
            tick_labels = []
            for pid in all_post_ids:
                post_item = id_map.get(pid, {})
                language = post_item.get("language") or "Unknown"
                tick_labels.append(f"{pid}\n[{language}]")
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=0, ha="center", fontsize=7)
            ax.set_title("Relative Timeline by Post (All Posts, Subreddit Colors)")
            ax.set_xlabel("Post ID")
            ax.set_ylabel("Hours Since Post (UTC)")
            ax.invert_yaxis()
            y_pad = max_hours_sub * 0.05
            ax.set_ylim(max_hours_sub + y_pad, -y_pad)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            # Legend for subreddits
            handles = [
                plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color_map[sub], markeredgecolor="black", markersize=7, label=sub)
                for sub in subreddits
            ]
            ax.legend(handles=handles, title="Subreddit", bbox_to_anchor=(1.02, 1), loc="upper left")
            ax.text(
                1.02,
                0.72,
                f"{sub_dropped} points > {max_hours_sub} hours not shown",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                color="#555555",
            )
            plt.tight_layout()
            plt.savefig(chart_timeline_relative_subreddit, dpi=300)
            plt.close()

            # Channelized version (separate lanes for post/comment/reply), no jitter
            plt.figure(figsize=(10, 5))
            ax = plt.gca()
            channel_offsets = {
                "post": channel_spacing,
                "comment": 0.0,
                "reply": -channel_spacing,
            }
            for delta_hours, item_type, root_post, item_id in filtered_points:
                item_obj = id_map.get(item_id) or {}
                color = _color_for_item(item_obj)
                if item_type == "post":
                    marker = "s"
                    size = 120
                elif item_type == "comment":
                    marker = "o"
                    size = 50
                else:
                    marker = "^"
                    size = 40
                base_y = rel_post_index.get(root_post, 0) * post_spacing
                ax.scatter(
                    delta_hours,
                    base_y + channel_offsets.get(item_type, 0.0),
                    c=[color],
                    marker=marker,
                    s=size,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=0.4,
                )
            ax.set_title("Timeline (Relative Time) by Post — Channelized")
            ax.set_xlabel("Hours Since Post (UTC)")
            ax.set_ylabel("Post Author")
            ax.set_yticks([idx * post_spacing for idx in range(len(rel_post_ids))])
            ax.set_yticklabels([_label_for_post(pid) for pid in rel_post_ids])
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            ax.legend(handles=shape_handles + color_handles, title="Legend", bbox_to_anchor=(1.02, 1), loc="upper left")
            plt.tight_layout()
            plt.savefig(chart_timeline_relative_channels, dpi=200)
            plt.close()
            if dropped_points:
                lines.append(f"- Notes: Dropped {dropped_points} points > {max_hours} hours to avoid axis compression.\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote crafting summary to: {output_path}")


if __name__ == "__main__":
    main()
