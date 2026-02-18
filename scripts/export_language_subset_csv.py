#!/usr/bin/env python3
"""Export a flattened CSV subset by language and inclusion rules.

Defaults to exporting Chinese/Chinese-adjacent languages + Unknown.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

DEFAULT_LANGUAGES = {
    "Chinese",
    "Mandarin",
    "Cantonese",
    "Hokkien",
    "Shanghainese",
    "Hakka",
    "Teochew",
    "Taiwanese",
}


def parse_parent_id(parent_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not parent_id:
        return None, None
    if "_" in parent_id:
        kind, pid = parent_id.split("_", 1)
        if kind == "t3":
            return "post", pid
        if kind == "t1":
            return "comment", pid
    return None, parent_id


def normalize_language(lang: Optional[str]) -> str:
    if not lang:
        return "Unknown"
    return str(lang).strip() or "Unknown"


def is_included(item: dict) -> bool:
    if item.get("not_relevant") is True:
        return False
    if item.get("include") is False:
        return False
    return True


def resolve_parent_post_id(
    item: dict, index: Dict[str, dict]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (parent_post_id, parent_comment_id, parent_kind)."""
    item_type = item.get("type")
    if item_type == "post":
        return item.get("id"), None, None

    parent_kind, parent_short_id = parse_parent_id(item.get("parent_id"))
    parent_comment_id = parent_short_id if parent_kind == "comment" else None

    if parent_kind == "post":
        return parent_short_id, parent_comment_id, parent_kind

    # Walk up comment chain to find the root post
    current_id = parent_short_id
    while current_id:
        parent_item = index.get(current_id)
        if not parent_item:
            break
        if parent_item.get("type") == "post":
            return parent_item.get("id"), parent_comment_id, parent_kind
        p_kind, p_short = parse_parent_id(parent_item.get("parent_id"))
        if p_kind == "post":
            return p_short, parent_comment_id, parent_kind
        if p_kind == "comment":
            current_id = p_short
        else:
            break

    return None, parent_comment_id, parent_kind


def to_iso(ts: Optional[float]) -> str:
    if ts is None:
        return ""
    try:
        return (
            dt.datetime.fromtimestamp(float(ts), tz=dt.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except Exception:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a flattened CSV subset of posts/comments/replies by language.")
    parser.add_argument(
        "--input",
        default="data/reddit_comments_replies_review.json",
        help="Path to reddit_comments_replies_review.json",
    )
    parser.add_argument(
        "--output",
        default="outputs/analysis/chinese_language_subset.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--languages",
        default=",".join(sorted(DEFAULT_LANGUAGES)),
        help="Comma-separated language list to include",
    )
    parser.add_argument(
        "--include-unknown",
        action="store_true",
        help="Include items with language Unknown (default: on)",
    )
    parser.add_argument(
        "--exclude-unknown",
        dest="include_unknown",
        action="store_false",
        help="Exclude items with language Unknown",
    )
    parser.set_defaults(include_unknown=True)
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open() as f:
        items = json.load(f)

    index = {it.get("id"): it for it in items if it.get("id")}

    # Determine which posts are included
    included_posts: Set[str] = set()
    for it in items:
        if it.get("type") == "post" and is_included(it):
            if it.get("id"):
                included_posts.add(it["id"])

    language_set = {lang.strip() for lang in args.languages.split(",") if lang.strip()}

    rows: List[dict] = []
    for it in items:
        if not is_included(it):
            continue

        lang = normalize_language(it.get("language"))
        if lang not in language_set and not (args.include_unknown and lang == "Unknown"):
            continue

        parent_post_id, parent_comment_id, parent_kind = resolve_parent_post_id(it, index)
        if it.get("type") in {"comment", "reply"}:
            if parent_post_id and parent_post_id not in included_posts:
                continue

        row = dict(it)
        row["language"] = lang
        row["parent_post_id"] = parent_post_id or ""
        row["parent_comment_id"] = parent_comment_id or ""
        row["parent_kind"] = parent_kind or ""
        row["created_iso"] = to_iso(it.get("created_utc"))
        rows.append(row)

    # Build column list: derived fields first, then all existing keys
    derived = ["parent_post_id", "parent_comment_id", "parent_kind", "created_iso"]
    keys: List[str] = []
    seen = set(derived)
    keys.extend(derived)

    for row in rows:
        for k in row.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
