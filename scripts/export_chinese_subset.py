#!/usr/bin/env python3
"""
Export a flattened CSV for Chinese/Chinese-adjacent HLL analysis.

Includes posts + comments + replies where language is in the specified list
or Unknown (optional), and where the parent post is included.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_LANGUAGES = [
    "mandarin",
    "cantonese",
    "hokkien",
    "shanghainese",
    "hakka",
    "teochew",
    "taiwanese",
    "chinese",
    "mandarinchinese",
    "mandarin chinese",
]


def _is_not_relevant(item: dict) -> bool:
    if item.get("not_relevant") is True:
        return True
    if item.get("exclude") is True:
        reason = (item.get("exclude_reason") or "").lower()
        if "not hll" in reason or "non-hll" in reason:
            return False
        return True
    return False


def _normalize_language(value: Optional[str]) -> str:
    if not value:
        return "unknown"
    return str(value).strip().lower()


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Chinese/adjacent HLL subset to CSV.")
    parser.add_argument(
        "--data",
        default="data/reddit_comments_replies_review.json",
        help="Path to review JSON.",
    )
    parser.add_argument(
        "--out",
        default="outputs/analysis/chinese_subset.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated list of languages to include (lowercase).",
    )
    parser.add_argument(
        "--include-unknown",
        action="store_true",
        help="Include items with language=Unknown.",
    )
    parser.add_argument(
        "--require-included-posts",
        action="store_true",
        help="Only include items whose parent post is explicitly include=true.",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if not _is_not_relevant(item)]
    id_map = {item.get("id"): item for item in data if item.get("id")}

    allowed_languages = {l.strip().lower() for l in args.languages.split(",") if l.strip()}
    include_unknown = args.include_unknown

    # Determine included posts (if required)
    allowed_post_ids = set()
    if args.require_included_posts:
        for item in data:
            if item.get("type") != "post":
                continue
            if item.get("include") is True and item.get("exclude") is not True:
                allowed_post_ids.add(item.get("id"))
    else:
        allowed_post_ids = {item.get("id") for item in data if item.get("type") == "post"}

    rows = []
    all_keys = set()

    for item in data:
        item_type = item.get("type")
        if item_type not in ("post", "comment", "reply"):
            continue

        language = _normalize_language(item.get("language"))
        language_ok = language in allowed_languages or (include_unknown and language == "unknown")
        if not language_ok:
            continue

        if item_type == "post":
            if item.get("id") not in allowed_post_ids:
                continue
            parent_post_id = item.get("id")
            parent_comment_id = ""
        else:
            parent_post_id = _root_post_id(item, id_map)
            if not parent_post_id or parent_post_id not in allowed_post_ids:
                continue
            if item_type == "comment":
                parent_comment_id = item.get("id")
            else:
                parent_id = item.get("parent_id") or ""
                parent_comment_id = parent_id[3:] if parent_id.startswith("t1_") else parent_id

        row = dict(item)
        row["language"] = item.get("language") or "Unknown"
        row["parent_post_id"] = parent_post_id
        row["parent_comment_id"] = parent_comment_id
        rows.append(row)
        all_keys.update(row.keys())

    fieldnames = sorted(all_keys)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
