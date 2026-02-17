#!/usr/bin/env python3
"""
CSV to JSON Converter for Comments Review Tool

Converts reddit_comments_replies_with_sentiment.csv into a JSON format
suitable for the comments review tool. Adds review fields for tracking
categorization decisions.

Input: data/reddit_comments_replies_with_sentiment.csv
Output: data/reddit_comments_replies_review.json

Review Fields Added:
- hll: Whether the poster is a Heritage Language Learner (boolean)
- non_hll: Whether the poster is explicitly Non-HLL (boolean)
- not_relevant: Whether the item is Not Relevant (boolean)
- adoptee: Whether the item indicates adoptee context (boolean)
- notes: Custom notes about the item (string)
- thematic_analysis: Whether item is relevant for thematic analysis (boolean)
- language: Language label for the item (string)

Usage:
    python3 scripts/csv_to_json_converter.py
"""

import csv
import json
from pathlib import Path
from typing import List, Dict


def load_csv(filepath: str) -> List[Dict]:
    """
    Load CSV file and convert to list of dictionaries.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        List[Dict]: List of dictionaries, one per row.
    """
    items = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(row)
        return items
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return []
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []


def add_review_fields(items: List[Dict]) -> List[Dict]:
    """
    Add review-related fields to each item.

    Args:
        items (List[Dict]): List of items from CSV.

    Returns:
        List[Dict]: Items with added review fields.
    """
    for item in items:
        if 'author' not in item:
            item['author'] = ''

        if 'is_op' not in item:
            item['is_op'] = False
        else:
            # Convert string to boolean if needed
            item['is_op'] = item['is_op'].lower() in ('true', '1', 'yes')

        # Add review fields if they don't exist
        if 'hll' not in item:
            item['hll'] = False
        else:
            # Convert string to boolean if needed
            item['hll'] = item['hll'].lower() in ('true', '1', 'yes')

        if 'notes' not in item:
            item['notes'] = ''

        if 'thematic_analysis' not in item:
            item['thematic_analysis'] = False
        else:
            # Convert string to boolean if needed
            item['thematic_analysis'] = item['thematic_analysis'].lower() in ('true', '1', 'yes')

        if 'non_hll' not in item:
            item['non_hll'] = False
        else:
            item['non_hll'] = item['non_hll'].lower() in ('true', '1', 'yes')

        if 'not_relevant' not in item:
            item['not_relevant'] = False
        else:
            item['not_relevant'] = item['not_relevant'].lower() in ('true', '1', 'yes')

        if 'adoptee' not in item:
            item['adoptee'] = False
        else:
            item['adoptee'] = item['adoptee'].lower() in ('true', '1', 'yes')

        if 'language' not in item or not item['language']:
            item['language'] = 'Unknown'

    return items


def convert_sentiment_scores(items: List[Dict]) -> List[Dict]:
    """
    Convert sentiment scores from strings to floats.

    Args:
        items (List[Dict]): List of items with string sentiment values.

    Returns:
        List[Dict]: Items with float sentiment values.
    """
    sentiment_fields = ['neg', 'neu', 'pos', 'compound']

    for item in items:
        for field in sentiment_fields:
            if field in item and item[field]:
                try:
                    item[field] = float(item[field])
                except ValueError:
                    item[field] = 0.0
            else:
                item[field] = 0.0

    return items


def convert_created_utc(items: List[Dict]) -> List[Dict]:
    for item in items:
        if "created_utc" not in item:
            continue
        value = item.get("created_utc")
        if value is None or value == "":
            item["created_utc"] = None
            continue
        try:
            item["created_utc"] = float(value)
        except ValueError:
            item["created_utc"] = None
    return items


def save_json(items: List[Dict], filepath: str) -> bool:
    """
    Save items to JSON file.

    Args:
        items (List[Dict]): Items to save.
        filepath (str): Output file path.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing JSON: {e}")
        return False


def main() -> None:
    """Main execution function."""
    # Define file paths - script lives in scripts/, data lives in data/
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / 'data'
    csv_file = data_dir / 'reddit_comments_replies_with_sentiment.csv'
    json_file = data_dir / 'reddit_comments_replies_review.json'

    print("=" * 60)
    print("CSV to JSON Converter")
    print("=" * 60)

    # Check if CSV file exists
    if not csv_file.exists():
        print(f"\nError: CSV file not found at {csv_file}")
        return

    print(f"\nInput:  {csv_file}")
    print(f"Output: {json_file}")

    # Load CSV
    print("\nLoading CSV...")
    items = load_csv(str(csv_file))

    if not items:
        print("No items loaded from CSV.")
        return

    print(f"Loaded {len(items)} items")

    # Convert sentiment scores to floats
    print("Converting sentiment scores...")
    items = convert_sentiment_scores(items)

    # Convert created_utc to float (if present)
    print("Converting created_utc...")
    items = convert_created_utc(items)

    # Add review fields
    print("Adding review fields...")
    items = add_review_fields(items)

    # Save JSON
    print("Saving JSON...")
    if save_json(items, str(json_file)):
        print(f"✓ Successfully saved {len(items)} items to {json_file}")
        
        # Print summary
        post_count = sum(1 for item in items if item.get('type') == 'post')
        comment_count = sum(1 for item in items if item.get('type') == 'comment')
        reply_count = sum(1 for item in items if item.get('type') == 'reply')
        
        print(f"\nItem Summary:")
        print(f"  Posts:    {post_count}")
        print(f"  Comments: {comment_count}")
        print(f"  Replies:  {reply_count}")
        print(f"  Total:    {len(items)}")
    else:
        print("✗ Error saving JSON file")


if __name__ == '__main__':
    main()
