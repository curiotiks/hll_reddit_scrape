#!/usr/bin/env python3
"""
Backfill created_utc timestamps into reddit_comments_replies_review.json.

Uses PRAW to fetch items by ID and merges timestamps without overwriting
any existing labels or review fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import sleep
from typing import Dict, Iterable, List

import praw


def load_meta(meta_path: Path) -> dict:
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_reddit(meta_path: Path) -> praw.Reddit:
    meta = load_meta(meta_path)
    return praw.Reddit(
        client_id=meta.get("client_id"),
        client_secret=meta.get("client_secret"),
        user_agent=meta.get("user_agent"),
        redirect_uri=meta.get("redirect_uri"),
    )


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def build_fullname(item: dict) -> str:
    item_type = item.get("type")
    item_id = item.get("id")
    if not item_id:
        return ""
    if item_type == "post":
        return f"t3_{item_id}"
    if item_type in ("comment", "reply"):
        return f"t1_{item_id}"
    return ""


def backfill_timestamps(
    data_path: Path,
    meta_path: Path,
    batch_size: int,
    sleep_seconds: float,
    backup: bool,
) -> None:
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a list in review JSON.")

    # Build list of fullnames to fetch where created_utc is missing
    fullnames = []
    index_by_fullname: Dict[str, List[int]] = {}
    for idx, item in enumerate(data):
        if item.get("created_utc") is not None:
            continue
        fullname = build_fullname(item)
        if not fullname:
            continue
        fullnames.append(fullname)
        index_by_fullname.setdefault(fullname, []).append(idx)

    if not fullnames:
        print("No missing created_utc fields found. Nothing to do.")
        return

    reddit = init_reddit(meta_path)

    fetched = 0
    for batch in chunked(fullnames, batch_size):
        for thing in reddit.info(fullnames=batch):
            fullname = thing.fullname
            created_utc = getattr(thing, "created_utc", None)
            if created_utc is None:
                continue
            for idx in index_by_fullname.get(fullname, []):
                data[idx]["created_utc"] = created_utc
            fetched += 1
        if sleep_seconds:
            sleep(sleep_seconds)

    if backup:
        backup_path = data_path.with_suffix(data_path.suffix + ".bak")
        data_path.replace(backup_path)
        data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Backup written to: {backup_path}")
        print(f"Updated file written to: {data_path}")
    else:
        data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated file written to: {data_path}")

    print(f"Items with created_utc backfilled: {fetched}")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Backfill created_utc timestamps.")
    parser.add_argument(
        "--data",
        type=Path,
        default=project_root / "data" / "reddit_comments_replies_review.json",
        help="Path to reddit_comments_replies_review.json",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        default=project_root / "meta_data.json",
        help="Path to meta_data.json (PRAW credentials)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Fullnames per API request batch.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds to sleep between batches.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable writing a .bak backup before updating.",
    )
    args = parser.parse_args()

    backfill_timestamps(
        data_path=args.data,
        meta_path=args.meta,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        backup=not args.no_backup,
    )


if __name__ == "__main__":
    main()
