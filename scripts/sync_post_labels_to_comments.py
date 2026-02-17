#!/usr/bin/env python3
"""
Sync post include/exclude labels into reddit_comments_replies_review.json and
propagate post exclusions to comments/replies.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def root_post_id(item, id_map):
    if item.get("type") == "post":
        return item.get("id")
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


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    posts_path = project_root / "data" / "posts.json"
    comments_path = project_root / "data" / "reddit_comments_replies_review.json"

    if not posts_path.exists() or not comments_path.exists():
        print("Missing posts.json or reddit_comments_replies_review.json")
        return

    posts_data = load_json(posts_path)
    comments = load_json(comments_path)

    post_labels = {}
    for _, items in posts_data.items():
        for item in items:
            post_id = item.get("id")
            if not post_id:
                continue
            post_labels[post_id] = {
                "include": bool(item.get("include", False)),
                "exclude": bool(item.get("exclude", False)),
                "reason": (item.get("reason") or "").strip(),
            }

    id_map = {item.get("id"): item for item in comments if item.get("id")}

    updated_posts = 0
    updated_children = 0

    for item in comments:
        post_id = root_post_id(item, id_map)
        if not post_id:
            continue

        labels = post_labels.get(post_id)
        if not labels:
            continue

        reason_text = labels["reason"].lower()
        exclude_as_non_hll = "not hll" in reason_text or "non-hll" in reason_text
        exclude_as_not_relevant = "not relevant" in reason_text or "nr" in reason_text

        if item.get("type") == "post":
            item["include"] = labels["include"]
            if labels["exclude"]:
                if exclude_as_non_hll:
                    item["non_hll"] = True
                else:
                    item["not_relevant"] = True
            if exclude_as_not_relevant:
                item["not_relevant"] = True
            updated_posts += 1
        else:
            if labels["exclude"]:
                item["not_relevant"] = True
                updated_children += 1

    save_json(comments_path, comments)
    print(f"Synced post labels to comments file: {comments_path}")
    print(f"Post items updated: {updated_posts}")
    print(f"Comments/replies excluded due to parent: {updated_children}")


if __name__ == "__main__":
    main()
