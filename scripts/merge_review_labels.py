#!/usr/bin/env python3
"""
Merge review labels from existing files into freshly re-scraped data.

Typical usage:
  1) Back up labeled files (old):
     cp data/posts.json data/posts.json.bak
     cp data/reddit_comments_replies_review.json data/reddit_comments_replies_review.json.bak

  2) Re-run scraping + sentiment + json conversion to refresh authors/OP.

  3) Merge labels back in:
     python3 scripts/merge_review_labels.py \
       --posts-old data/posts.json.bak --posts-new data/posts.json \
       --posts-out data/posts.json \
       --comments-old data/reddit_comments_replies_review.json.bak \
       --comments-new data/reddit_comments_replies_review.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

POST_REVIEW_FIELDS = ["include", "exclude", "reason", "is_new"]
COMMENT_REVIEW_FIELDS = [
    "hll",
    "non_hll",
    "not_relevant",
    "adoptee",
    "notes",
    "thematic_analysis",
    "language",
    "created_utc",
    "is_new",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data, indent: int) -> None:
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")


def build_post_review_map(old_data: Dict) -> Dict[str, Dict]:
    review_map = {}
    for _, items in old_data.items():
        for item in items:
            post_id = item.get("id")
            if post_id:
                review_map[post_id] = {
                    field: item.get(field) for field in POST_REVIEW_FIELDS if field in item
                }
    return review_map


def merge_posts(old_data: Dict, new_data: Dict) -> Tuple[Dict, Dict[str, int]]:
    review_map = build_post_review_map(old_data)
    new_ids = set()
    merged_count = 0
    for _, items in new_data.items():
        for item in items:
            post_id = item.get("id")
            if not post_id:
                continue
            new_ids.add(post_id)
            review_fields = review_map.get(post_id)
            if review_fields:
                for field, value in review_fields.items():
                    item[field] = value
                # Preserve existing is_new state (default to False if missing)
                item["is_new"] = bool(review_fields.get("is_new", False))
                merged_count += 1
            else:
                # New post in this scrape
                item["is_new"] = True
    # Preserve old posts that are not in the new scrape
    added_old = 0
    for old_key, old_items in old_data.items():
        for item in old_items:
            post_id = item.get("id")
            if not post_id or post_id in new_ids:
                continue
            item["is_new"] = False
            new_data.setdefault(old_key, []).append(item)
            added_old += 1
    # De-duplicate posts by id across all groups
    seen = set()
    deduped = 0
    for key, items in new_data.items():
        deduped_items = []
        for item in items:
            post_id = item.get("id")
            if not post_id:
                continue
            if post_id in seen:
                deduped += 1
                continue
            seen.add(post_id)
            deduped_items.append(item)
        new_data[key] = deduped_items
    report = {
        "posts_merged": merged_count,
        "posts_added_old": added_old,
        "posts_deduped": deduped,
        "posts_total": len(seen),
    }
    return new_data, report


def build_comment_review_map(old_items: List[Dict]) -> Dict[Tuple[str, str], Dict]:
    review_map = {}
    for item in old_items:
        item_id = item.get("id")
        item_type = item.get("type")
        if item_id and item_type:
            review_map[(item_id, item_type)] = {
                field: item.get(field) for field in COMMENT_REVIEW_FIELDS if field in item
            }
    return review_map


def merge_comments(old_items: List[Dict], new_items: List[Dict]) -> Tuple[List[Dict], Dict[str, int]]:
    review_map = build_comment_review_map(old_items)
    new_keys = set()
    merged_count = 0
    for item in new_items:
        item_id = item.get("id")
        item_type = item.get("type")
        if not item_id or not item_type:
            continue
        key = (item_id, item_type)
        new_keys.add(key)
        review_fields = review_map.get(key)
        if review_fields:
            for field, value in review_fields.items():
                item[field] = value
            # Preserve existing is_new state (default to False if missing)
            item["is_new"] = bool(review_fields.get("is_new", False))
            merged_count += 1
        else:
            # New item in this scrape
            item["is_new"] = True
    # Preserve old items that are not in the new scrape
    added_old = 0
    for item in old_items:
        item_id = item.get("id")
        item_type = item.get("type")
        if not item_id or not item_type:
            continue
        key = (item_id, item_type)
        if key in new_keys:
            continue
        item["is_new"] = False
        new_items.append(item)
        added_old += 1
    # De-duplicate by (id, type) after merge
    seen = set()
    deduped = []
    deduped_count = 0
    for item in new_items:
        item_id = item.get("id")
        item_type = item.get("type")
        if not item_id or not item_type:
            continue
        key = (item_id, item_type)
        if key in seen:
            deduped_count += 1
            continue
        seen.add(key)
        deduped.append(item)
    report = {
        "comments_merged": merged_count,
        "comments_added_old": added_old,
        "comments_deduped": deduped_count,
        "comments_total": len(seen),
    }
    return deduped, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge review labels into fresh data.")
    parser.add_argument("--posts-old", type=Path, help="Old labeled posts.json")
    parser.add_argument("--posts-new", type=Path, help="Newly scraped posts.json")
    parser.add_argument("--posts-out", type=Path, help="Output posts.json")
    parser.add_argument(
        "--posts-out-review",
        type=Path,
        help="Optional: also write merged posts.json to review_app",
    )
    parser.add_argument("--comments-old", type=Path, help="Old labeled review JSON")
    parser.add_argument("--comments-new", type=Path, help="New review JSON")
    parser.add_argument("--comments-out", type=Path, help="Output review JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    if args.posts_old and args.posts_new and args.posts_out:
        old_posts = load_json(args.posts_old)
        new_posts = load_json(args.posts_new)
        merged_posts, post_report = merge_posts(old_posts, new_posts)
        write_json(args.posts_out, merged_posts, indent=4)
        print(f"✓ Merged posts written to {args.posts_out}")
        if args.posts_out_review:
            write_json(args.posts_out_review, merged_posts, indent=4)
            print(f"✓ Merged posts written to {args.posts_out_review}")
        print(
            "Post merge report: "
            f"merged={post_report['posts_merged']}, "
            f"added_old={post_report['posts_added_old']}, "
            f"deduped={post_report['posts_deduped']}, "
            f"total={post_report['posts_total']}"
        )
        report["posts"] = post_report

    if args.comments_old and args.comments_new:
        comments_out = args.comments_out or args.comments_new
        old_comments = load_json(args.comments_old)
        new_comments = load_json(args.comments_new)
        merged_comments, comment_report = merge_comments(old_comments, new_comments)
        write_json(comments_out, merged_comments, indent=2)
        print(f"✓ Merged comments written to {comments_out}")
        print(
            "Comment merge report: "
            f"merged={comment_report['comments_merged']}, "
            f"added_old={comment_report['comments_added_old']}, "
            f"deduped={comment_report['comments_deduped']}, "
            f"total={comment_report['comments_total']}"
        )
        report["comments"] = comment_report

    if "posts" in report:
        report["posts"]["posts_new_flagged"] = 0
        report["posts"]["posts_reviewed"] = 0
        if args.posts_out:
            merged_posts = load_json(args.posts_out)
            for _, items in merged_posts.items():
                for item in items:
                    if item.get("is_new"):
                        report["posts"]["posts_new_flagged"] += 1
                    else:
                        report["posts"]["posts_reviewed"] += 1

    if "comments" in report and args.comments_out:
        report["comments"]["comments_new_flagged"] = 0
        report["comments"]["comments_reviewed"] = 0
        merged_comments = load_json(args.comments_out)
        for item in merged_comments:
            if item.get("is_new"):
                report["comments"]["comments_new_flagged"] += 1
            else:
                report["comments"]["comments_reviewed"] += 1

    if report.keys() != {"generated_at"}:
        project_root = Path(__file__).resolve().parent.parent
        report_dir = project_root / "outputs" / "meta-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"merge_report_{stamp}.json"
        write_json(report_path, report, indent=2)
        print(f"✓ Merge report written to {report_path}")


if __name__ == "__main__":
    main()
