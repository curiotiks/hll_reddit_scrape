#!/usr/bin/env python3
"""
Affinity space analysis (Volume + Engagement).

Outputs:
  - outputs/analysis/affinity/volume_summary.md
  - outputs/analysis/affinity/engagement_summary.md
  - outputs/analysis/affinity/affinity_summary.md
"""

from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import praw


def _is_not_relevant(item: dict) -> bool:
    if item.get("not_relevant") is True:
        return True
    if item.get("exclude") is True:
        reason = (item.get("exclude_reason") or "").lower()
        if "not hll" in reason or "non-hll" in reason:
            return False
        return True
    return False


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _median(values: Iterable[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return statistics.median(vals)


def _fmt(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def _pct(value: Optional[float], digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}%"


def _item_text(item: dict) -> str:
    if item.get("type") == "post":
        title = item.get("title") or ""
        body = item.get("body") or ""
        return (title + "\n\n" + body).strip()
    return (item.get("body") or "").strip()


def _root_post_id(item: dict, id_map: dict) -> Optional[str]:
    current = item
    seen = set()
    while current and current.get("type") != "post":
        parent_id = current.get("parent_id") or ""
        if not parent_id:
            return None
        if parent_id.startswith("t3_"):
            parent_id = parent_id[3:]
        elif parent_id.startswith("t1_"):
            parent_id = parent_id[3:]
        if parent_id in seen:
            return None
        seen.add(parent_id)
        current = id_map.get(parent_id)
    return current.get("id") if current else None


def _group_key(item: dict) -> Optional[str]:
    if item.get("hll") is True:
        return "hll"
    if item.get("non_hll") is True:
        return "non_hll"
    return None


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "reddit_comments_replies_review.json"
    posts_path = project_root / "data" / "posts.json"
    meta_path = project_root / "meta_data.json"
    output_dir = project_root / "outputs" / "analysis" / "affinity"
    output_dir.mkdir(parents=True, exist_ok=True)

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if not _is_not_relevant(item)]

    id_map = {item.get("id"): item for item in data if item.get("id")}
    posts = [item for item in data if item.get("type") == "post"]
    comments_replies = [item for item in data if item.get("type") in ("comment", "reply")]

    # Map post -> subreddit (and full scraped post list)
    post_id_to_subreddit = {}
    posts_by_subreddit = {}
    all_scraped_posts = []
    if posts_path.exists():
        with posts_path.open("r", encoding="utf-8") as f:
            posts_data = json.load(f)
        for subreddit, items in posts_data.items():
            if not isinstance(items, list):
                continue
            posts_by_subreddit[subreddit] = items
            all_scraped_posts.extend(items)
            for item in items:
                post_id = item.get("id")
                if post_id:
                    post_id_to_subreddit[post_id] = subreddit

    # Root post mapping for comments/replies
    root_post_by_item = {}
    for item in comments_replies:
        root_post_by_item[item.get("id")] = _root_post_id(item, id_map)

    # Responses per post (exclude OP replies)
    responses_per_post = {}
    for item in comments_replies:
        if item.get("is_op") is True:
            continue
        root_post = root_post_by_item.get(item.get("id"))
        if not root_post:
            continue
        responses_per_post[root_post] = responses_per_post.get(root_post, 0) + 1

    # Word counts
    post_word_counts = {item.get("id"): _word_count(_item_text(item)) for item in posts}
    comment_word_counts = [_word_count(_item_text(item)) for item in comments_replies]

    # Grouped item buckets
    grouped = {
        "all": data,
        "hll": [i for i in data if i.get("hll") is True],
        "non_hll": [i for i in data if i.get("non_hll") is True],
    }

    # ---- Volume summary ----
    volume_lines = []
    volume_lines.append("# Affinity Space: Volume\n")
    volume_lines.append(
        "Counts and median word counts within the discovered HLL discussion space. "
        "For subreddit‑level comparisons, see the adapted Table 1 in affinity_summary.md."
    )
    volume_lines.append("")

    volume_lines.append("| Group | Posts | Comments | Replies | Total | Median Post Words | Median Comment Words | Median Reply Words |")
    volume_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, items in grouped.items():
        posts_g = [i for i in items if i.get("type") == "post"]
        comments_g = [i for i in items if i.get("type") == "comment"]
        replies_g = [i for i in items if i.get("type") == "reply"]
        total_g = len(posts_g) + len(comments_g) + len(replies_g)
        post_wc = [_word_count(_item_text(i)) for i in posts_g]
        comment_wc = [_word_count(_item_text(i)) for i in comments_g]
        reply_wc = [_word_count(_item_text(i)) for i in replies_g]
        volume_lines.append(
            f"| {label.upper()} | {len(posts_g)} | {len(comments_g)} | {len(replies_g)} | {total_g} | "
            f"{_fmt(_median(post_wc), 1)} | {_fmt(_median(comment_wc), 1)} | {_fmt(_median(reply_wc), 1)} |"
        )
    volume_lines.append("")
    # HLL share of total matched content
    all_items = grouped["all"]
    hll_items = grouped["hll"]
    total_all = len(all_items)
    total_hll = len(hll_items)
    total_posts_all = len([i for i in all_items if i.get("type") == "post"])
    total_posts_hll = len([i for i in hll_items if i.get("type") == "post"])
    total_cr_all = len([i for i in all_items if i.get("type") in ("comment", "reply")])
    total_cr_hll = len([i for i in hll_items if i.get("type") in ("comment", "reply")])
    total_posts_scraped = len([p for p in all_scraped_posts if isinstance(p, dict)])
    volume_lines.append("| HLL Share | Posts | Comments/Replies | Total |")
    volume_lines.append("|---|---:|---:|---:|")
    volume_lines.append(
        f"| HLL / All | {_pct((total_posts_hll / total_posts_scraped * 100) if total_posts_scraped else None)} | "
        f"{_pct((total_cr_hll / total_cr_all * 100) if total_cr_all else None)} | "
        f"{_pct((total_hll / total_all * 100) if total_all else None)} |"
    )
    volume_lines.append("")

    # ---- Engagement summary ----
    engagement_lines = []
    engagement_lines.append("# Affinity Space: Engagement\n")
    engagement_lines.append(
        "Engagement metrics reported for All/HLL/Non‑HLL, plus HLL share. "
        "HLL share for posts uses all scraped posts as the denominator."
    )
    engagement_lines.append("")

    engagement_lines.append("| Group | Posts | Response Rate | Median Responses/Post | Median Post Score | Median Comment Score | Median Reply Score |")
    engagement_lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for label in ("all", "hll", "non_hll"):
        posts_g = [p for p in posts if (label == "all" or _group_key(p) == label)]
        if posts_g:
            post_ids = [p.get("id") for p in posts_g if p.get("id")]
        else:
            post_ids = []
        if not post_ids:
            continue
        response_counts = [responses_per_post.get(pid, 0) for pid in post_ids]
        responded = sum(1 for c in response_counts if c > 0)
        response_rate = (responded / len(post_ids) * 100) if post_ids else None

        post_scores = [_to_float(p.get("score")) for p in posts_g]
        comment_scores = [
            _to_float(i.get("score"))
            for i in comments_replies
            if (label == "all" or _group_key(i) == label) and i.get("type") == "comment"
        ]
        reply_scores = [
            _to_float(i.get("score"))
            for i in comments_replies
            if (label == "all" or _group_key(i) == label) and i.get("type") == "reply"
        ]

        engagement_lines.append(
            f"| {label.upper()} | {len(post_ids)} | {_pct(response_rate)} | {_fmt(_median(response_counts), 1)} | "
            f"{_fmt(_median(post_scores), 1)} | {_fmt(_median(comment_scores), 1)} | {_fmt(_median(reply_scores), 1)} |"
        )
    engagement_lines.append("")
    # HLL share of engagement (using All as denominator)
    all_posts = [p for p in posts]
    hll_posts = [p for p in posts if _group_key(p) == "hll"]
    all_post_ids = [p.get("id") for p in all_posts if p.get("id")]
    hll_post_ids = [p.get("id") for p in hll_posts if p.get("id")]
    all_response_counts = [responses_per_post.get(pid, 0) for pid in all_post_ids]
    hll_response_counts = [responses_per_post.get(pid, 0) for pid in hll_post_ids]
    all_responded = sum(1 for c in all_response_counts if c > 0)
    hll_responded = sum(1 for c in hll_response_counts if c > 0)
    engagement_lines.append("| HLL Share | HLL Posts / All Scraped Posts | Responses/Post |")
    engagement_lines.append("|---|---:|---:|")
    engagement_lines.append(
        f"| HLL / All | {_pct((len(hll_post_ids) / total_posts_scraped * 100) if total_posts_scraped else None)} | "
        f"{_pct((sum(hll_response_counts) / sum(all_response_counts) * 100) if sum(all_response_counts) else None)} |"
    )

    # ---- Subreddit breakdowns ----
    def subreddit_table(title: str, posts_subset: list[dict]) -> list[str]:
        lines = []
        lines.append(f"## {title}\n")
        lines.append("| Subreddit | Scraped Posts | HLL Posts (n, %) | Response Rate | Median Responses/Post | Median Post Words | Median Post Score |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")

        rows = {}
        for post in posts_subset:
            post_id = post.get("id")
            if not post_id:
                continue
            subreddit = post_id_to_subreddit.get(post_id)
            if not subreddit:
                continue
            rows.setdefault(subreddit, []).append(post)

        for subreddit in sorted(rows.keys()):
            posts_here = rows[subreddit]
            post_ids = [p.get("id") for p in posts_here if p.get("id")]
            response_counts = [responses_per_post.get(pid, 0) for pid in post_ids]
            responded = sum(1 for c in response_counts if c > 0)
            response_rate = (responded / len(post_ids) * 100) if post_ids else None
            post_words = [_word_count(_item_text(p)) for p in posts_here]
            post_scores = [_to_float(p.get("score")) for p in posts_here]
            scraped_posts = [p for p in posts_by_subreddit.get(subreddit, []) if isinstance(p, dict)]
            scraped_total = len(scraped_posts)
            hll_count = len([p for p in posts_here if p.get("hll") is True])
            hll_pct = (hll_count / scraped_total * 100) if scraped_total else None
            lines.append(
                f"| {subreddit} | {scraped_total} | {hll_count} ({_pct(hll_pct)}) | {_pct(response_rate)} | "
                f"{_fmt(_median(response_counts), 1)} | {_fmt(_median(post_words), 1)} | {_fmt(_median(post_scores), 1)} |"
            )
        lines.append("")
        return lines

    engagement_lines.extend(subreddit_table("Subreddit Breakdown (All Posts)", posts))
    engagement_lines.extend(
        subreddit_table(
            "Subreddit Breakdown (HLL Posts)",
            [p for p in posts if _group_key(p) == "hll"],
        )
    )
    engagement_lines.extend(
        subreddit_table(
            "Subreddit Breakdown (Non‑HLL Posts)",
            [p for p in posts if _group_key(p) == "non_hll"],
        )
    )

    # ---- Table 1 style summary (adapted) ----
    table1_lines = []
    table1_lines.append("# Table 1 (Adapted): Volume + Engagement by Subreddit\n")
    table1_lines.append(
        "Adapted from Staudt Willet & Na (2024). Scraped posts reflect the newest 100 posts per subreddit; "
        "these scraped posts are already keyword‑matched by design. Engagement metrics use these matched posts "
        "and their comments/replies. Non‑relevant items are excluded."
    )
    table1_lines.append("")

    # Load subreddit subscriber counts
    subscribers_by_subreddit = {}
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)
        try:
            reddit = praw.Reddit(
                client_id=meta.get("client_id"),
                client_secret=meta.get("client_secret"),
                user_agent=meta.get("user_agent"),
                redirect_uri=meta.get("redirect_uri"),
            )
            for subreddit in posts_by_subreddit.keys():
                try:
                    subscribers_by_subreddit[subreddit] = reddit.subreddit(subreddit).subscribers
                except Exception:
                    subscribers_by_subreddit[subreddit] = None
        except Exception:
            subscribers_by_subreddit = {}

    # Pre-compute comment/reply word counts per root post
    comment_word_counts_by_post = {}
    total_comments_by_post = {}
    for item in comments_replies:
        root_post = root_post_by_item.get(item.get("id"))
        if not root_post:
            continue
        total_comments_by_post[root_post] = total_comments_by_post.get(root_post, 0) + 1
        comment_word_counts_by_post.setdefault(root_post, []).append(_word_count(_item_text(item)))

    table1_lines.append(
        "| Subreddit | Subscribers | Scraped Posts (Matched) | HLL Posts n (%) | "
        "Median Thread Length | Median Post Words | Median Comment Words | "
        "Median Post Score | Total Comments/Replies | Earliest Matched Post |"
    )
    table1_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")

    # Build per-subreddit rows, sorted by total comments/replies
    sub_stats = []
    for subreddit, items in posts_by_subreddit.items():
        post_ids_sample = [p.get("id") for p in items if p.get("id")]
        total_posts_sample = len(post_ids_sample)

        review_posts = [
            p for p in posts
            if post_id_to_subreddit.get(p.get("id")) == subreddit
        ]
        review_post_ids = [p.get("id") for p in review_posts if p.get("id")]

        hll_posts = [p for p in review_posts if p.get("hll") is True]

        hll_pct = (len(hll_posts) / total_posts_sample * 100) if total_posts_sample else None

        response_counts = [responses_per_post.get(pid, 0) for pid in review_post_ids]
        responded = sum(1 for c in response_counts if c > 0)
        response_rate = (responded / len(review_post_ids) * 100) if review_post_ids else None

        post_words = [_word_count(_item_text(p)) for p in review_posts]
        post_scores = [_to_float(p.get("score")) for p in review_posts]
        thread_lengths = response_counts

        total_comments = sum(total_comments_by_post.get(pid, 0) for pid in review_post_ids)
        comment_words = []
        for pid in review_post_ids:
            comment_words.extend(comment_word_counts_by_post.get(pid, []))

        earliest_date = None
        for post in review_posts:
            created = post.get("created_utc")
            if created is None:
                continue
            try:
                dt = datetime.fromtimestamp(float(created), tz=timezone.utc)
            except Exception:
                continue
            if earliest_date is None or dt < earliest_date:
                earliest_date = dt

        sub_stats.append({
            "subreddit": subreddit,
            "subscribers": subscribers_by_subreddit.get(subreddit),
            "total_posts_sample": total_posts_sample,
            "hll_posts": len(hll_posts),
            "hll_pct": hll_pct,
            "median_post_words": _median(post_words),
            "response_rate": response_rate,
            "median_thread": _median(thread_lengths),
            "median_post_score": _median(post_scores),
            "total_comments": total_comments,
            "median_comment_words": _median(comment_words),
            "earliest": earliest_date,
        })

    sub_stats.sort(key=lambda r: r["total_comments"], reverse=True)

    for row in sub_stats:
        earliest_str = row["earliest"].strftime("%Y-%m-%d") if row["earliest"] else "—"
        hll_str = f"{row['hll_posts']} ({_pct(row['hll_pct'])})"
        subscribers = row["subscribers"] if row["subscribers"] is not None else "—"
        table1_lines.append(
            f"| {row['subreddit']} | {subscribers} | {row['total_posts_sample']} | "
            f"{hll_str} | {_fmt(row['median_thread'], 1)} | "
            f"{_fmt(row['median_post_words'], 1)} | {_fmt(row['median_comment_words'], 1)} | "
            f"{_fmt(row['median_post_score'], 1)} | {row['total_comments']} | {earliest_str} |"
        )
    table1_lines.append("")

    # ---- Combined short summary ----
    affinity_lines = []
    affinity_lines.append("# Affinity Space Summary\n")
    affinity_lines.append(
        "This report aligns our dataset with the Affinity Space framework (volume + engagement). "
        "We scraped the newest 100 posts per subreddit, then matched posts by inclusive keyword search. "
        "Engagement metrics use matched posts and their comments/replies. Non‑relevant items are excluded; "
        "response counts exclude OP replies. Response rates were uniformly high, so they are summarized in text rather than shown in the table."
    )
    affinity_lines.append("")
    affinity_lines.append("## Table 1 (Adapted): Volume + Engagement by Subreddit\n")
    affinity_lines.extend(table1_lines[3:])  # include table header + rows
    affinity_lines.append("")
    affinity_lines.append("**Poster-ready summary (text):**")
    affinity_lines.append(
        "We analyzed the newest 100 posts per subreddit and identified HLL‑relevant discussions via an inclusive keyword search. "
        "Across subreddits, HLL posts constitute a small share of total scraped posts, but they draw sustained engagement as reflected in "
        "median thread lengths and comment volume. Because response rates were consistently high, we emphasize thread length and word‑count medians "
        "to compare engagement intensity rather than whether posts received a response at all."
    )
    affinity_lines.append("")
    affinity_lines.append("## Overall Volume (Matched Sample)\n")
    affinity_lines.append("| Group | Posts | Comments | Replies | Total | Median Post Words | Median Comment Words | Median Reply Words |")
    affinity_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, items in grouped.items():
        posts_g = [i for i in items if i.get("type") == "post"]
        comments_g = [i for i in items if i.get("type") == "comment"]
        replies_g = [i for i in items if i.get("type") == "reply"]
        total_g = len(posts_g) + len(comments_g) + len(replies_g)
        post_wc = [_word_count(_item_text(i)) for i in posts_g]
        comment_wc = [_word_count(_item_text(i)) for i in comments_g]
        reply_wc = [_word_count(_item_text(i)) for i in replies_g]
        affinity_lines.append(
            f"| {label.upper()} | {len(posts_g)} | {len(comments_g)} | {len(replies_g)} | {total_g} | "
            f"{_fmt(_median(post_wc), 1)} | {_fmt(_median(comment_wc), 1)} | {_fmt(_median(reply_wc), 1)} |"
        )
    affinity_lines.append("")

    # Write outputs (single file)
    (output_dir / "affinity_summary.md").write_text("\n".join(affinity_lines), encoding="utf-8")

    print(f"Wrote affinity summaries to: {output_dir}")


if __name__ == "__main__":
    main()
