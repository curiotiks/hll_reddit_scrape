# Crafting Summary

- Source: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/data/reddit_comments_replies_review.json`

- Generated: 2026-02-16 19:21

## Comments/Replies per Post (excluding OP replies)

Number of posts: 26

| Metric | Mean | Median | Std Dev | Min | Max | n |
|---|---|---|---|---|---|---|
| count_per_post | 11.1154 | 5.5000 | 15.5649 | 0.0000 | 68.0000 | 26 |

## Subreddit Activity Summary

| Subreddit | HLL Posts | All Posts | Avg Score (HLL Posts) | Avg Comments/Replies per Post |
|---|---|---|---|---|

| Cantonese | 2 | 2 | 40.00 | 24.00 |
| Chinese | 1 | 1 | 7.00 | 6.00 |
| ChineseLanguage | 2 | 2 | 4.50 | 3.33 |
| LearnANewLanguage | 1 | 1 | 5.00 | — |
| LearnCantonese | 1 | 1 | 17.00 | 7.00 |
| LearningMandarin | 1 | 1 | 3.00 | — |
| asianamerican | 4 | 4 | 12.75 | 4.75 |
| hakka | 1 | 1 | 16.00 | 7.00 |
| languagelearning | 7 | 7 | 29.86 | 7.71 |
| shanghainese | 1 | 1 | 25.00 | 13.00 |

## Visuals

### Comments/Replies: eHLL vs Non-HLL

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/comments_replies_ehll_vs_nonehll.png`

- Description: Percent of total comments/replies authored by eHLL vs Non‑HLL.

- Notes: Based on comment/reply counts (not unique authors).

### Cross‑Posting by eHLL Authors

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/cross_posting_histogram.png`

- Description: Histogram of the number of distinct posts each eHLL author commented/replied to.

- Notes: Comments/replies only; excludes OP replies.

### Timeline (Absolute)

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/timeline_posts_absolute.png`

- Description: Posts only over absolute time (UTC), y‑axis = post author [language].

- Notes: Uses jitter to reduce overlap.

### Timeline (Relative)

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/timeline_posts_relative.png`

- Description: Posts/comments/replies over hours since post, y‑axis = post author [language].

- Notes: Top 10 posts by total comments/replies; shapes denote type (post/comment/reply); colors denote HLL vs Non‑HLL.

### Timeline (Relative, Rotated Waterfall)

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/timeline_posts_relative_rotated.png`

- Description: Same data as relative timeline, rotated (x = post order by date, y = hours since post), ordered by post date.

- Notes: Top 10 posts by total comments/replies; no jitter; drops points > 150 hours; time increases downward; bottom labels = author; years grouped with subtle separators; channels separated left-to-right (post/comment/reply).

### Timeline (Relative, Channelized)

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/timeline_posts_relative_channels.png`

- Description: Same data as relative timeline with separate lanes for post/comment/reply.

- Notes: Top 10 posts by total comments/replies; no jitter; extra spacing between posts and lanes.

### Timeline (Relative, All Posts by Subreddit)

- File: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/outputs/analysis/timeline_posts_relative_subreddit.png`

- Description: All posts/comments/replies; colors indicate subreddit, shapes indicate type.

- Notes: Points > 150 hours not shown.

## Cross-posting by eHLL Authors (Comments/Replies Only)

- Definition: for each eHLL author, count how many different posts they commented/replied to (excluding OP replies).

### eHLL Authors and Posts Participated In

| eHLL Author | # of Posts Commented/Replied To | Post IDs |
|---|---|---|
| [deleted] | 4 | 14ac5gz, 18mlyse, 1ql15io, vod156 |
| Lotuswongtko | 2 | 1qfmcit, 1qu9ne5 |
| Other (1 post) | 75 | — |

- Notes: Dropped 6 points > 800 hours to avoid axis compression.
