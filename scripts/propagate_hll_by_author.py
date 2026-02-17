#!/usr/bin/env python3
"""
Propagate HLL tags across all items by author.

1) Build a set of authors with hll == True.
2) Mark hll == True for every item whose author is in that set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() == "true"


def _load_metadata(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _write_metadata(path: Path, meta: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)


def _load_included_post_authors(posts_path: Path) -> set[str]:
    if not posts_path.exists():
        return set()
    with posts_path.open("r", encoding="utf-8") as f:
        posts_data = json.load(f)
    authors = set()
    if not isinstance(posts_data, dict):
        return authors
    for posts in posts_data.values():
        if not isinstance(posts, list):
            continue
        for post in posts:
            if not isinstance(post, dict):
                continue
            if post.get("include") is True and post.get("exclude") is not True:
                author = (post.get("author") or "").strip()
                if author:
                    authors.add(author)
    return authors


def propagate_hll(json_path: Path, output_path: Path, meta_path: Path, posts_path: Path) -> None:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a list of items in the review JSON.")

    meta = _load_metadata(meta_path)
    hll_authors = set(meta.get("hll_authors", []))
    included_post_authors = _load_included_post_authors(posts_path)
    hll_authors |= included_post_authors
    for item in data:
        author = (item.get("author") or "").strip()
        if not author:
            continue
        if _as_bool(item.get("hll")):
            hll_authors.add(author)

    updated = 0
    for item in data:
        author = (item.get("author") or "").strip()
        if not author:
            continue
        if (
            author in hll_authors
            and not _as_bool(item.get("hll"))
            and not _as_bool(item.get("non_hll"))
        ):
            item["hll"] = True
            updated += 1

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    meta["hll_authors"] = sorted(hll_authors)
    _write_metadata(meta_path, meta)

    print("HLL propagation complete.")
    print(f"  Total items: {len(data)}")
    print(f"  HLL authors: {len(hll_authors)}")
    print(f"  Included post authors added: {len(included_post_authors)}")
    print(f"  Newly updated items: {updated}")
    print(f"  Output: {output_path}")
    print(f"  Metadata updated: {meta_path}")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    default_json = project_root / "data" / "reddit_comments_replies_review.json"
    default_posts = project_root / "data" / "posts.json"

    parser = argparse.ArgumentParser(
        description="Propagate HLL tags across all items by author."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=default_json,
        help="Path to reddit_comments_replies_review.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path. Defaults to in-place update.",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        default=project_root / "meta_data.json",
        help="Path to meta_data.json (for writing hll_authors list).",
    )
    parser.add_argument(
        "--posts",
        type=Path,
        default=default_posts,
        help="Path to posts.json (for included post authors).",
    )
    args = parser.parse_args()

    output_path = args.output or args.input
    propagate_hll(args.input, output_path, args.meta, args.posts)


if __name__ == "__main__":
    main()
