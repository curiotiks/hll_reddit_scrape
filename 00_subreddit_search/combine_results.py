import pandas as pd
import glob

def merge_csv_files():
    """
    Merges all CSV files in the current directory into a single DataFrame.
    """
    csv_files = glob.glob("*.csv")
    if not csv_files:
        print("No CSV files found in the current directory.")
        return None
    
    return pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

def create_summary_table(df):
    """
    Counts occurrences, sums subscribers, and picks the latest UTC date per Name.
    """
    if df is None:
        print("No DataFrame to summarize.")
        return None

    # 1) Ensure your date column is datetime
    df['Last Post Date/Time (UTC)'] = pd.to_datetime(
        df['Last Post Date/Time (UTC)'],
        utc=True,
        errors='coerce'          # turn invalid parses into NaT
    )

    # 2) Count how many times each Name appears
    name_counts = (
        df['Name']
        .value_counts()
        .reset_index(name='Count')
        .rename(columns={'index': 'Name'})
    )

    # 3) Sum subscriber counts per Name
    subscriber_sum = (
        df
        .groupby('Name', as_index=False)['Number of Subscribers']
        .sum()
        .rename(columns={'Number of Subscribers': 'Subscriber Total'})
    )

    # 4) Get the most recent post date per Name
    last_post = (
        df
        .groupby('Name', as_index=False)['Last Post Date/Time (UTC)']
        .max()
    )
    
    # 5) Add the Subreddit description
    sub_description = (
        df
        .groupby('Name', as_index=False)['Description']
        .first()  # or use .agg(lambda x: ' '.join(x)) to concatenate descriptions
    )
    
    # Optional: format back to string if you prefer
    last_post['Last Post Date/Time (UTC)'] = last_post[
        'Last Post Date/Time (UTC)'
    ].dt.strftime('%Y-%m-%d %H:%M:%S')

    # 5) Merge them all together
    summary = (
        name_counts
        .merge(subscriber_sum, on='Name')
        .merge(last_post, on='Name')
        .merge(sub_description, on='Name')
    )
    
    # Sort by Count (descending) then Subscriber Total (descending)
    summary = summary.sort_values(by=['Count', 'Subscriber Total'], ascending=[False, False])

    return summary

if __name__ == "__main__":
    combined_df = merge_csv_files()
    summary_table = create_summary_table(combined_df)
    if summary_table is not None:
        print(summary_table)
        summary_table.to_csv("summary.csv", index=False)