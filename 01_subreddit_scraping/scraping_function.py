import argparse
import csv
import json
import time
from pathlib import Path

import praw
import prawcore


def initialize_reddit(filepath):
    with open(filepath, 'r') as file:
        meta_data = json.load(file)

        csv_file = meta_data.get('csv_file')

        reddit = praw.Reddit(
            client_id=meta_data.get('client_id'),
            client_secret=meta_data.get('client_secret'),
            user_agent=meta_data.get('user_agent'),
            redirect_uri=meta_data.get('redirect_uri')
        )

        url_list = meta_data.get('reddit_post_urls') or []

    return reddit, csv_file, url_list


def get_post_details(submission):
    post_data = {
        "title": submission.title,
        "author": submission.author.name if submission.author else "[deleted]",
        "score": submission.score,
        "id": submission.id,
        "url": submission.url,
        "num_comments": submission.num_comments,
        "created_utc": submission.created_utc,
        "body": submission.selftext
    }
    return post_data

def get_comments(submission):
    submission.comments.replace_more(limit=None)
    comments_data = []
    # Only top-level comments; replies handled separately to avoid duplicates
    for comment in submission.comments:
        comments_data.append({
            "id": comment.id,
            "author": comment.author.name if comment.author else "[deleted]",
            "is_op": bool(comment.is_submitter),
            "body": comment.body,
            "score": comment.score,
            "created_utc": comment.created_utc,
            "parent_id": comment.parent_id,
            "replies": get_replies(comment)
        })
    return comments_data

def get_replies(comment):
    replies_data = []
    if hasattr(comment, "replies"):
        comment.replies.replace_more(limit=None)
        for reply in comment.replies.list():
            replies_data.append({
                "id": reply.id,
                "author": reply.author.name if reply.author else "[deleted]",
                "is_op": bool(reply.is_submitter),
                "body": reply.body,
                "score": reply.score,
                "created_utc": reply.created_utc,
                "parent_id": reply.parent_id
            })
    return replies_data

def scrape_reddit_post(reddit, url, max_retries=3, backoff_seconds=5):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            submission = reddit.submission(url=url)
            post_details = get_post_details(submission)
            comments = get_comments(submission)
            return {
                "post_details": post_details,
                "comments": comments
            }
        except prawcore.exceptions.RequestException as err:
            last_error = err
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
                continue
            raise
        except Exception as err:
            last_error = err
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
                continue
            raise
    if last_error:
        raise last_error
    return None

def process_comments(comments, data_list, is_reply=False):
    for comment in comments:
        comment_id = comment.get('id')
        comment_author = comment.get('author', '')
        comment_is_op = bool(comment.get('is_op', False))
        comment_body = comment.get('body', '')
        comment_score = comment.get('score', 0)
        comment_parent_id = comment.get('parent_id', '')
        comment_type = 'reply' if is_reply else 'comment'
        
        data_list.append({
            'id': comment_id,
            'type': comment_type,
            'score': comment_score,
            'parent_id': comment_parent_id,
            'title': '',
            'body': comment_body,
            'author': comment_author,
            'is_op': comment_is_op,
            'created_utc': comment.get('created_utc')
        })
        
        # Process replies
        if 'replies' in comment:
            process_comments(comment['replies'], data_list, is_reply=True)

def load_included_post_urls(posts_path: Path) -> list[str]:
    if not posts_path.exists():
        return []
    with posts_path.open('r', encoding='utf-8') as f:
        posts_data = json.load(f)
    urls = []
    for posts in posts_data.values():
        if not isinstance(posts, list):
            continue
        for post in posts:
            if not isinstance(post, dict):
                continue
            include = post.get('include') is True
            exclude = post.get('exclude') is True
            if include and not exclude and post.get('url'):
                urls.append(post['url'])
    return sorted(set(urls))


def main():
    parser = argparse.ArgumentParser(
        description="Scrape comments/replies for a list of Reddit post URLs."
    )
    parser.add_argument(
        "--use-included-posts",
        action="store_true",
        help="Use included posts from data/posts.json instead of meta_data.json reddit_post_urls."
    )
    parser.add_argument(
        "--posts-json",
        default=None,
        help="Optional path to posts.json (default: data/posts.json)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds to wait between post fetches."
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per post when request fails."
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    meta_path = project_root / 'meta_data.json'
    connection, _, url_list = initialize_reddit(str(meta_path))

    if args.use_included_posts:
        posts_path = Path(args.posts_json) if args.posts_json else project_root / "data" / "posts.json"
        included_urls = load_included_post_urls(posts_path)
        if included_urls:
            url_list = included_urls
        else:
            print("Warning: No included posts found in posts.json; falling back to meta_data.json URLs.")

    if not url_list:
        print("Error: No URLs available for scraping.")
        return

    data_list = []

    for idx, each_url in enumerate(url_list, start=1):
        try:
            scraped_data = scrape_reddit_post(
                connection,
                each_url,
                max_retries=args.max_retries
            )
        except Exception as err:
            print(f"Error scraping {each_url}: {err}")
            continue

        post_details = scraped_data['post_details']

        data_list.append({
            'id': post_details.get('id'),
            'type': 'post',
            'score': post_details.get('score', 0),
            'parent_id': '',
            'title': post_details.get('title', ''),
            'body': post_details.get('body', ''),
            'author': post_details.get('author', ''),
            'is_op': True,
            'created_utc': post_details.get('created_utc')
        })

        process_comments(scraped_data['comments'], data_list)
        print(f"[{idx}/{len(url_list)}] items so far: {len(data_list)}")
        time.sleep(args.delay)

    deduped = []
    seen = set()
    for item in data_list:
        key = (item.get('id'), item.get('type'))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    csv_file = data_dir / 'reddit_comments_replies.csv'
    csv_columns = ['id', 'type', 'score', 'parent_id', 'title', 'body', 'author', 'is_op', 'created_utc']

    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(deduped)

    print(f"Data has been scraped and saved to {csv_file}")


if __name__ == "__main__":
    main()
