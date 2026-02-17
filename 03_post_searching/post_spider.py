"""
post_spider.py

This script ingests a list of subreddit URLs from meta_data.json and collects posts from each subreddit using the PRAW library. The output will append post URLs to the existing meta_data.json file.

This script:
- Reads list of subreddits from meta_data.json ("sub_urls").
- Uses PRAW to fetch posts from each subreddit with matching keywords from "post_search_keywords".
- Appends post URLs to meta_data.json.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse

import praw
from keyword_sets import HERITAGE_LANGUAGE_KEYWORDS

def initialize_reddit(filepath):
    with open(filepath, 'r') as file: 
        meta_data = json.load(file)
        
        reddit = praw.Reddit(client_id=meta_data.get('client_id'),
                             client_secret=meta_data.get('client_secret'),
                             user_agent=meta_data.get('user_agent'),
                             redirect_uri=meta_data.get('redirect_uri'))

    return reddit, meta_data

def extract_subreddit_name(sub_url):
    parsed = urlparse(sub_url)
    parts = [part for part in parsed.path.split('/') if part]
    if "r" in parts:
        idx = parts.index("r")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return sub_url.strip().rstrip("/")

def summarize_selftext(selftext, max_lines=10, max_chars=1000):
    if not selftext:
        return ""
    lines = [line.strip() for line in selftext.splitlines() if line.strip()]
    snippet = "\n".join(lines[:max_lines])
    return snippet[:max_chars]

def update_posts_file(reddit, sub_urls, keywords, output_path, limit=100):
    if not sub_urls:
        print("Error: sub_urls not found in meta")
        return

    if not keywords:
        print("Error: keywords cannot be empty")
        return

    posts_by_subreddit = {}

    for sub_url in sub_urls:
        subreddit_name = extract_subreddit_name(sub_url)
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = []

            """
            A notable limitation to our searching method. This does not scan the comments of each post, only the title and selftext. Which means single comments left by HLL on posts not directly related may be missed. 

            TODO: Implement comment scanning in future iterations.
            """
            
            for submission in subreddit.new(limit=limit):
                if any(keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower() for keyword in keywords):
                    post_data = {
                        "title": submission.title,
                        "id": submission.id,
                        "url": submission.url,
                        "author": submission.author.name if submission.author else "[deleted]",
                        "created_utc": datetime.fromtimestamp(
                            submission.created_utc, tz=timezone.utc
                        ).isoformat(),
                        "num_comments": submission.num_comments,
                        "selftext_snippet": summarize_selftext(submission.selftext),
                        "include": False, # Placeholder for manual review
                        "exclude": False,  # Placeholder for manual review
                        "reason": ""  # Placeholder for manual review
                    }
                    posts.append(post_data)

            posts_by_subreddit[subreddit_name] = posts
            print(f"Successfully fetched {len(posts)} posts from r/{subreddit_name}")
    
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit_name}: {e}")

    with open(output_path, 'w') as file:
        json.dump(posts_by_subreddit, file, indent=4)


if __name__ == '__main__':
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    meta_path = project_root / 'meta_data.json'

    reddit, meta = initialize_reddit(str(meta_path))
    
    sub_urls = meta.get('sub_urls', [])
    keywords = HERITAGE_LANGUAGE_KEYWORDS
    
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    output_path = data_dir / 'posts.json'
    update_posts_file(reddit, sub_urls, keywords, str(output_path))
