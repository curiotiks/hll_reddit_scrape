"""
Reddit Sentiment Analysis Script

This script performs sentiment analysis on Reddit posts, comments, and replies
using VADER (Valence Aware Dictionary and sEntiment Reasoner), a lexicon and
rule-based sentiment analysis tool optimized for social media text.

The script reads comment and reply data from a CSV file, analyzes the sentiment
of each text body, and outputs the results with sentiment scores (positive,
negative, neutral, and compound) appended as new columns.

Required Input:
    - data/reddit_comments_replies.csv: CSV file containing posts, comments, and
      replies with columns including 'body' (text to analyze)

Output:
    - data/reddit_comments_replies_with_sentiment.csv: CSV file with all original
      columns plus sentiment score columns (positive, negative, neutral, compound)

Dependencies:
    - pandas: For data manipulation
    - nltk: For VADER sentiment analysis

Author: Research Team
Date: January 26, 2026
"""

import pandas as pd
from pathlib import Path
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import Dict


def get_sentiment(text: str) -> Dict[str, float]:
    """
    Compute sentiment scores for a given text using VADER sentiment analyzer.

    VADER returns four sentiment metrics:
    - positive: Proportion of text expressing positive sentiment (0-1)
    - negative: Proportion of text expressing negative sentiment (0-1)
    - neutral: Proportion of text expressing neutral sentiment (0-1)
    - compound: Normalized composite sentiment score (-1 to 1)
      * compound >= 0.05: Positive
      * compound <= -0.05: Negative
      * -0.05 < compound < 0.05: Neutral

    Args:
        text (str): The text to analyze for sentiment.

    Returns:
        Dict[str, float]: Dictionary containing sentiment scores with keys:
                         'neg', 'neu', 'pos', and 'compound'
    """
    return sid.polarity_scores(text)


def main() -> None:
    """
    Main execution function.

    Loads Reddit comments and replies data, performs sentiment analysis on
    each text body, and saves the enhanced dataset with sentiment scores.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / 'data'
    input_file = data_dir / 'reddit_comments_replies.csv'
    output_file = data_dir / 'reddit_comments_replies_with_sentiment.csv'

    # Load the data from the CSV file into a DataFrame
    print(f"Loading {input_file.name}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records")

    # Initialize the VADER sentiment analyzer
    print("Initializing VADER sentiment analyzer...")
    global sid
    sid = SentimentIntensityAnalyzer()

    # Apply sentiment analysis to each comment/reply body
    print("Analyzing sentiment for all text entries...")
    df['sentiment'] = df['body'].apply(get_sentiment)

    # Split sentiment scores into separate columns
    print("Expanding sentiment scores into individual columns...")
    df = pd.concat(
        [df.drop(['sentiment'], axis=1), df['sentiment'].apply(pd.Series)],
        axis=1
    )

    # Save the DataFrame with sentiment scores to a new CSV file
    print(f"Saving results to {output_file}...")
    df.to_csv(output_file, index=False)

    print(f"Sentiment analysis completed successfully!")
    print(f"Output file: {output_file}")
    print(f"Total records processed: {len(df)}")


if __name__ == '__main__':
    main()
