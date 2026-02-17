#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

POSTS_REVIEW="$ROOT/data/posts.json"
COMMENTS_REVIEW="$ROOT/data/reddit_comments_replies_review.json"

STAMP="$(date +%Y%m%d_%H%M%S)"
POSTS_BAK="$ROOT/data/posts.json.bak.$STAMP"
COMMENTS_BAK="$ROOT/data/reddit_comments_replies_review.json.bak.$STAMP"

echo "==> Backing up labeled files"
cp "$POSTS_REVIEW" "$POSTS_BAK"
cp "$COMMENTS_REVIEW" "$COMMENTS_BAK"
echo "✓ Backup posts:    $POSTS_BAK"
echo "✓ Backup comments: $COMMENTS_BAK"

echo "\n==> Re-scraping posts (authors for post reviewer)"
"$ROOT/.venv/bin/python" "$ROOT/03_post_searching/post_spider.py"

echo "\n==> Re-scraping comments/replies (authors + OP)"
"$ROOT/.venv/bin/python" "$ROOT/01_subreddit_scraping/scraping_function.py"

echo "\n==> Recomputing sentiment"
"$ROOT/.venv/bin/python" "$ROOT/01_subreddit_scraping/reddit_sentiment.py"

echo "\n==> Converting CSV to review JSON"
"$ROOT/.venv/bin/python" "$ROOT/scripts/csv_to_json_converter.py"

echo "\n==> Merging labels back in"
"$ROOT/.venv/bin/python" "$ROOT/scripts/merge_review_labels.py" \
  --posts-old "$POSTS_BAK" --posts-new "$ROOT/data/posts.json" \
  --posts-out "$ROOT/data/posts.json" \
  --comments-old "$COMMENTS_BAK" --comments-new "$ROOT/data/reddit_comments_replies_review.json"

echo "\n==> Syncing post labels into comments/replies"
"$ROOT/.venv/bin/python" "$ROOT/scripts/sync_post_labels_to_comments.py"

echo "\n✓ Done. Data refreshed and labels merged."
