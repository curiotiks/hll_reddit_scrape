# Analysis of Reddit Discussions: Chinese Heritage Language Learning

**Wenting Song** and **Curt "The Forgotten" Fulwider** (EPLS)

## Poster Summary
We used an inclusive keyword search (OR logic) to identify heritage‑language–relevant discussions in selected language‑learning subreddits, scraping the newest 100 posts per subreddit via the Reddit API and collecting linked comments/replies and metadata. Posts were manually labeled for inclusion, HLL status, and language in a reviewer app; labels were propagated to associated comments/replies, and non‑relevant items were excluded from analysis. The poster focuses on Chinese‑related HLL content only (Mandarin + related varieties), with a final dataset of **n = 71**.

We conducted manual thematic analysis on the included posts, comments, and replies to generate the theme categories and percentages reported. Volume and engagement are summarized by subreddit for matched HLL posts, reflecting relative visibility and participation across the sampled subreddits.

## Methods (Process Overview)
1. **Search & scrape:** Inclusive keyword search (OR logic) across selected language‑learning subreddits; scrape newest 100 posts per subreddit and collect all linked comments/replies plus metadata.
1. **Screening & labeling:** Manually review posts for inclusion, HLL status, and language in a reviewer app.
1. **Propagation:** Apply post labels to associated comments/replies; remove non‑relevant items from analysis.
1. **Thematic analysis:** Code the included Chinese‑related HLL content to derive theme categories and percentages.

## Results (Poster Tables)
- **Volume and Engagement by Subreddit (HLL‑Matched Posts Only):** `outputs/analysis/affinity/apa_tables/table1_volume_engagement_apa7.pdf`
- **Themes and Percent of Posts:** `outputs/analysis/affinity/apa_tables/themes_apa7.pdf`

## Repository Contents
- `00_subreddit_search/`, `03_post_searching/`: keyword discovery and post sampling
- `01_subreddit_scraping/`: comment/reply scraping and sentiment utilities
- `04_analysis/`: analysis scripts (inventory, crafting, affinity, thematic)
- `scripts/`: utilities for merging, exporting, and regeneration
- `outputs/analysis/affinity/`: aggregate tables (APA‑ready)
- `outputs/analysis/*.png`: aggregate figures used in the poster
- `meta_data.example.json`: template for local credentials and settings

## Reproduction (Local)
1. Copy `meta_data.example.json` → `meta_data.json` and add your Reddit API credentials.
1. Run `03_post_searching/` and `01_subreddit_scraping/` to rebuild data.
1. Use analysis scripts in `04_analysis/` to regenerate tables/figures.

## Ethics & Privacy
This public repo **excludes raw data and text excerpts** to prevent searchable usernames or post content. Only aggregate outputs (tables/figures) are included for the poster framework.
