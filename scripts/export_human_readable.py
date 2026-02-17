#!/usr/bin/env python3
"""
Export human-readable CSVs for posts and comments/replies with a timestamp.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "outputs" / "human_readable"
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    posts_out = output_dir / f"posts_flattened_{stamp}.csv"
    comments_out = output_dir / f"comments_replies_review_{stamp}.csv"

    posts_path = data_dir / "posts.json"
    comments_path = data_dir / "reddit_comments_replies_review.json"

    if posts_path.exists():
        posts_data = json.loads(posts_path.read_text(encoding="utf-8"))
        rows = []
        for subreddit, items in posts_data.items():
            for item in items:
                row = {"subreddit": subreddit}
                row.update(item)
                rows.append(row)
        fieldnames = sorted({k for row in rows for k in row.keys()})
        with posts_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    if comments_path.exists():
        comments_data = json.loads(comments_path.read_text(encoding="utf-8"))
        if comments_data:
            fieldnames = [
                "id",
                "type",
                "parent_id",
                "author",
                "is_op",
                "score",
                "title",
                "body",
                "created_utc",
                "neg",
                "neu",
                "pos",
                "compound",
                "hll",
                "non_hll",
                "not_relevant",
                "adoptee",
                "thematic_analysis",
                "language",
                "notes",
                "is_new",
            ]
            # Include any extra keys not in the default list
            extras = sorted({k for item in comments_data for k in item.keys()} - set(fieldnames))
            fieldnames.extend(extras)
            with comments_out.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(comments_data)

    print(f"Wrote: {posts_out}")
    print(f"Wrote: {comments_out}")


if __name__ == "__main__":
    main()
