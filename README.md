# Heritage Language Learning on Reddit (Public Repo)

This public repository contains the **code and analysis pipeline** for a study of heritage‑language learning discussions on Reddit. **Data, outputs, review tools, and posters are excluded** to protect participants and keep the repo lightweight.

## Study Overview
- **Goal:** Examine volume, engagement, and content of heritage‑language (HLL) discussions across language‑learning subreddits.
- **Approach:** Inclusive keyword search of recent posts, manual labeling of HLL status, and analysis of response patterns and topic themes.
- **Framework:** Affinity Space lens (volume + engagement), plus thematic/BERTopic content analysis.

## Data Collection (High‑Level)
1. Scrape the newest 100 posts per subreddit.
1. Keep posts whose title or self‑text match **any** keyword (inclusive OR).
1. Manually label posts (HLL vs Non‑HLL, language, relevance).
1. Scrape all comments/replies for included posts and run sentiment + topic analysis.

## Key Results (Summary)
- HLL‑relevant posts are a **small share** of scraped posts, but generate **sustained engagement** (thread length and comment volume).
- Response rates are **consistently high** across subreddits, so engagement intensity is best reflected in **thread length and word‑count medians**.
- Topic modeling and thematic analysis surface **recurring motivations, identity tension, and learning barriers**.

## Public Repository Contents
- `00_subreddit_search/`, `03_post_searching/`: keyword and post discovery logic
- `01_subreddit_scraping/`: comment/reply scraping and sentiment analysis
- `04_analysis/`: analysis scripts (inventory, crafting, affinity, thematic)
- `scripts/`: utilities for merging and conversion
- `meta_data.example.json`: template for local credentials and settings

## Local Setup (For Reproduction)
1. Copy `meta_data.example.json` → `meta_data.json` and add your Reddit API credentials.
1. Install dependencies in a local virtual environment.
1. Run the scripts in `03_post_searching/`, `01_subreddit_scraping/`, and `04_analysis/` as needed.

## Q/A (Conference‑Style)
**Q: What is the sampling frame?**  
A: We scrape the newest 100 posts per subreddit and retain posts that match at least one keyword. This prioritizes recent, relevant discussions.

**Q: Does this represent all subreddit activity?**  
A: No. It is a matched‑post sample, not the full subreddit population. We report this as a limitation.

**Q: How is HLL defined?**  
A: HLL status is manually labeled based on self‑identification or clear contextual cues in posts/comments.

**Q: How do you handle ethics and privacy?**  
A: Only public posts are collected; no raw data is released in this public repo; sensitive data is excluded.

**Q: What about bots or deleted users?**  
A: Deleted authors remain in metadata as `[deleted]`. Content is included only if available at scrape time.

**Q: Why not include the review UI and data?**  
A: The public repo focuses on code and methods. The review UI and labeled data are restricted due to privacy and IRB considerations.

**Q: How reproducible are the results?**  
A: The pipeline is reproducible given access to the same subreddit snapshot and credentials. Results may shift over time due to Reddit content changes.

**Q: Why use BERTopic and thematic analysis together?**  
A: BERTopic provides topic structure; thematic analysis interprets and consolidates those patterns into human‑meaningful themes.

**Q: What are the main limitations?**  
A: Reddit users are not representative of all HLLs; the sample is time‑bounded and keyword‑filtered; moderation and deletion can affect visibility.
