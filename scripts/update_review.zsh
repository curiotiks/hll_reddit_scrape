#!/bin/zsh

# Get the root directory (script's parent directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
ROOT_POSTS="$ROOT_DIR/data/posts.json"
REVIEW_APP_DIR="$ROOT_DIR/review_app"
ARCHIVE_DIR="$REVIEW_APP_DIR/archive"

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Get current date in YYYY-MM-DD format
DATE=$(date +%Y-%m-%d)

# Create filename with date
DATED_FILENAME="posts_${DATE}.json"
DATED_PATH="$ARCHIVE_DIR/$DATED_FILENAME"

# Check if data/posts.json exists
if [ ! -f "$ROOT_POSTS" ]; then
    echo "✗ Error: $ROOT_POSTS not found"
    exit 1
fi

# Copy and rename to archive with date
cp "$ROOT_POSTS" "$DATED_PATH"
echo "✓ Archived to: $DATED_PATH"

echo "✓ Done! Archive updated. Review app reads from data/posts.json now."
