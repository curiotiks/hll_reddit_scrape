#!/usr/bin/env python3
"""
Migrate review tags from legacy exclude/exclude_reason to new fields:
  - non_hll (Non-HLL)
  - not_relevant (N/R)
Also ensure language defaults to "Unknown" when missing.
"""

from __future__ import annotations

import json
from pathlib import Path


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def _infer_from_exclude(item: dict) -> tuple[bool, bool, str]:
    """Return (non_hll, not_relevant, reason_used)."""
    exclude = _as_bool(item.get("exclude"))
    if not exclude:
        return False, False, ""
    reason = (item.get("exclude_reason") or "").strip().lower()
    if "not hll" in reason or "non-hll" in reason:
        return True, False, reason
    return False, True, reason or "legacy_exclude"


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    json_path = project_root / "data" / "reddit_comments_replies_review.json"

    if not json_path.exists():
        print(f"Missing file: {json_path}")
        return

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a list of items.")

    converted = 0
    non_hll_count = 0
    not_rel_count = 0
    lang_defaulted = 0

    for item in data:
        if "mandarin" in item:
            item.pop("mandarin", None)
        if "non_hll" in item or "not_relevant" in item:
            # Still ensure language exists
            if not item.get("language"):
                item["language"] = "Unknown"
                lang_defaulted += 1
            continue

        non_hll, not_rel, _reason = _infer_from_exclude(item)
        item["non_hll"] = bool(non_hll)
        item["not_relevant"] = bool(not_rel)
        if item["non_hll"]:
            non_hll_count += 1
        if item["not_relevant"]:
            not_rel_count += 1

        if not item.get("language"):
            item["language"] = "Unknown"
            lang_defaulted += 1

        if "exclude" in item:
            item.pop("exclude", None)
        if "exclude_reason" in item:
            item.pop("exclude_reason", None)
        converted += 1

    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Migration complete.")
    print(f"  Items updated: {converted}")
    print(f"  non_hll set: {non_hll_count}")
    print(f"  not_relevant set: {not_rel_count}")
    print(f"  language defaulted: {lang_defaulted}")
    print(f"  Output: {json_path}")


if __name__ == "__main__":
    main()
