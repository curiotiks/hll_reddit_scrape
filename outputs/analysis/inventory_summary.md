# Inventory Summary

- Source: `/Users/curtfulwider/Documents/Research/HL_reddit_scrap/data/reddit_comments_replies_review.json`

- Generated: 2026-02-15 20:36

## How To Read This Summary

### Slices

- Slice A: Posts by evident HLLs (`type=post`, `hll=true`).

- Slice B: Comments/replies by evident HLLs excluding OP replies (`type in {comment, reply}`, `hll=true`, `is_op=false`).

- Slice C: Comments/replies by non‑HLLs (`type in {comment, reply}`, `non_hll=true`).

- Slice Z: Entire dataset (excluding N/R).

### Variables

- `neg`, `neu`, `pos`: VADER sentiment proportions for negative, neutral, and positive tone (0–1).

- `compound`: VADER composite sentiment score (−1 to 1), where higher is more positive overall.

- `score`: Reddit score (upvotes minus downvotes).

## Slice A: Posts by evident HLLs

Count of posts: 26

| Metric | Mean | Median | Std Dev | Min | Max | n |
|---|---|---|---|---|---|---|
| neg | 0.0640 | 0.0610 | 0.0540 | 0.0000 | 0.1980 | 26 |
| neu | 0.8291 | 0.8320 | 0.0631 | 0.7170 | 0.9730 | 26 |
| pos | 0.1070 | 0.1095 | 0.0459 | 0.0230 | 0.1950 | 26 |
| compound | 0.2743 | 0.7713 | 0.8006 | -0.9724 | 0.9878 | 26 |
| score | 23.2308 | 8.0000 | 39.5417 | 0.0000 | 180.0000 | 26 |

## Slice B: Comments/Replies by evident HLLs (excluding OP replies)

Count of comments/replies: 112

| Metric | Mean | Median | Std Dev | Min | Max | n |
|---|---|---|---|---|---|---|
| neg | 0.0751 | 0.0610 | 0.0787 | 0.0000 | 0.4980 | 112 |
| neu | 0.8047 | 0.8135 | 0.0873 | 0.5020 | 1.0000 | 112 |
| pos | 0.1203 | 0.1115 | 0.0728 | 0.0000 | 0.3560 | 112 |
| compound | 0.3505 | 0.6731 | 0.6626 | -0.9641 | 0.9987 | 112 |
| score | 7.5625 | 3.0000 | 13.2378 | 0.0000 | 85.0000 | 112 |

## Slice C: Comments/Replies by non-HLLs

Count of comments/replies: 88

| Metric | Mean | Median | Std Dev | Min | Max | n |
|---|---|---|---|---|---|---|
| neg | 0.0493 | 0.0315 | 0.0682 | 0.0000 | 0.3550 | 88 |
| neu | 0.8414 | 0.8475 | 0.1177 | 0.4610 | 1.0000 | 88 |
| pos | 0.1093 | 0.0970 | 0.1093 | 0.0000 | 0.5390 | 88 |
| compound | 0.3338 | 0.4117 | 0.5081 | -0.7871 | 0.9987 | 88 |
| score | 4.2727 | 2.0000 | 5.8304 | -2.0000 | 37.0000 | 88 |

## Slice Z: Entire Dataset (excluding N/R)

Count of items: 280

| Metric | Mean | Median | Std Dev | Min | Max | n |
|---|---|---|---|---|---|---|
| neg | 0.0590 | 0.0390 | 0.0765 | 0.0000 | 0.4980 | 280 |
| neu | 0.8037 | 0.8210 | 0.1273 | 0.2180 | 1.0000 | 280 |
| pos | 0.1373 | 0.1115 | 0.1270 | 0.0000 | 0.7820 | 280 |
| compound | 0.3512 | 0.5568 | 0.6081 | -0.9724 | 0.9987 | 280 |
| score | 6.8464 | 2.0000 | 15.9331 | -2.0000 | 180.0000 | 280 |
