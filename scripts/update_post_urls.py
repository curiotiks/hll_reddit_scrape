#!/usr/bin/env python3
"""
Update Post URLs Script

This script extracts URLs from the data/posts.json file and adds them to
the reddit_post_urls list in meta_data.json. It handles deduplication by only
adding URLs that are not already present in the meta_data.json file.

Usage:
    python update_post_urls.py

Author: Research Team
Date: January 26, 2026
"""

import json
import os
from pathlib import Path
from typing import List, Set


def load_json_file(file_path: str) -> dict:
    """
    Load and parse a JSON file.

    Args:
        file_path (str): Path to the JSON file to load.

    Returns:
        dict: Parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(file_path: str, data: dict, indent: int = 4) -> None:
    """
    Save data to a JSON file with proper formatting.

    Args:
        file_path (str): Path to the file to save.
        data (dict): Dictionary to save as JSON.
        indent (int): Number of spaces for indentation. Defaults to 4.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def extract_urls_from_posts(posts_data: dict) -> Set[str]:
    """
    Extract URLs from posts.json, filtering by include/exclude criteria.

    The posts.json file has a structure where each key is a subreddit name,
    and the value is a list of post objects. Only posts with include=True and
    exclude=False are included. Posts with conflicting states (both True) will
    generate a warning but will not be included.

    Args:
        posts_data (dict): The loaded posts.json data.

    Returns:
        Set[str]: A set of unique URLs that meet the inclusion criteria.
    """
    urls = set()

    for subreddit, posts in posts_data.items():
        if isinstance(posts, list):
            for post in posts:
                if isinstance(post, dict) and 'url' in post:
                    url = post['url']
                    if not url:  # Skip empty URLs
                        continue

                    # Check inclusion criteria
                    include = post.get('include', False)
                    exclude = post.get('exclude', False)

                    # Flag conflicting states
                    if include and exclude:
                        title = post.get('title', 'Unknown')
                        print(f"Warning: Conflicting state for post '{title}' "
                              f"in r/{subreddit}: include=True AND exclude=True. "
                              f"Skipping this URL.")
                        continue

                    # Only add URLs where include=True and exclude=False
                    if include and not exclude:
                        urls.add(url)

    return urls


def update_metadata_urls(posts_urls: Set[str], meta_data: dict) -> int:
    """
    Update the reddit_post_urls list in meta_data with new URLs.

    Args:
        posts_urls (Set[str]): Set of URLs from posts.json.
        meta_data (dict): The loaded meta_data.json data.

    Returns:
        int: Number of new URLs added.
    """
    # Ensure the reddit_post_urls list exists
    if 'reddit_post_urls' not in meta_data:
        meta_data['reddit_post_urls'] = []

    # Convert existing URLs to a set for efficient lookup
    existing_urls = set(meta_data['reddit_post_urls'])

    # Find new URLs to add
    new_urls = posts_urls - existing_urls

    # Add new URLs to the list
    meta_data['reddit_post_urls'].extend(sorted(new_urls))

    return len(new_urls)


def remove_duplicate_urls(meta_data: dict) -> int:
    """
    Remove duplicate URLs from the reddit_post_urls list in meta_data.

    Args:
        meta_data (dict): The loaded meta_data.json data.

    Returns:
        int: Number of duplicate URLs removed.
    """
    if 'reddit_post_urls' not in meta_data:
        return 0

    original_count = len(meta_data['reddit_post_urls'])
    # Convert to set to remove duplicates, then back to sorted list
    meta_data['reddit_post_urls'] = sorted(set(meta_data['reddit_post_urls']))
    duplicates_removed = original_count - len(meta_data['reddit_post_urls'])

    return duplicates_removed


def main() -> None:
    """
    Main execution function.

    Loads posts.json and meta_data.json, extracts URLs from posts.json,
    updates meta_data.json with any new URLs, and saves the changes.
    """
    # Define file paths
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    posts_json_path = project_root / 'data' / 'posts.json'
    meta_data_path = project_root / 'meta_data.json'

    # Validate file existence
    if not posts_json_path.exists():
        print(f"Error: File not found: {posts_json_path}")
        return

    if not meta_data_path.exists():
        print(f"Error: File not found: {meta_data_path}")
        return

    try:
        # Load JSON files
        print("Loading files...")
        posts_data = load_json_file(str(posts_json_path))
        meta_data = load_json_file(str(meta_data_path))

        # Extract URLs from posts.json
        print("Extracting URLs from posts.json...")
        posts_urls = extract_urls_from_posts(posts_data)
        print(f"Found {len(posts_urls)} unique URLs in posts.json")

        # Update meta_data.json
        print("Updating meta_data.json...")
        new_count = update_metadata_urls(posts_urls, meta_data)
        print(f"Added {new_count} new URLs to reddit_post_urls")

        # Remove any duplicate URLs
        print("Checking for and removing duplicates...")
        duplicates_removed = remove_duplicate_urls(meta_data)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate URLs")
        else:
            print("No duplicates found")

        # Save updated meta_data.json
        print("Saving meta_data.json...")
        save_json_file(str(meta_data_path), meta_data)
        print(f"Successfully updated {meta_data_path}")
        print(f"Total URLs in reddit_post_urls: {len(meta_data['reddit_post_urls'])}")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in one of the files: {e}")
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")


if __name__ == '__main__':
    main()
