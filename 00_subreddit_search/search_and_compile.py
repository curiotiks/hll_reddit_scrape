import praw
import json
import pandas as pd
from datetime import datetime, timezone

def initialize_reddit(filepath):
    with open(filepath, 'r') as file: 
        meta_data = json.load(file)

        csv_file = meta_data.get('csv_file')
        
        reddit = praw.Reddit(client_id=meta_data.get('client_id'),
                             client_secret=meta_data.get('client_secret'),
                             user_agent=meta_data.get('user_agent'),
                             redirect_uri=meta_data.get('redirect_uri'))

    return reddit, csv_file

reddit, csv_file = initialize_reddit('meta_data.json')

languages = [
    "English", "Spanish", "Mandarin", "Chinese", "French", "German", 
    "Japanese", "Italian", "Portuguese", "Russian", "Korean",
    "Arabic", "Hindi", "Turkish", "Dutch", "Swedish",
    "Polish", "Greek", "Hebrew", "Vietnamese", "Thai",
    "Ukrainian", "Romanian", "Cantonese", "Indonesian", "Tamil",
    "Bengali", "Czech", "Hungarian", "Farsi (Persian)", "Tagalog",
    "Malay", "Danish", "Norwegian", "Finnish", "Serbian",
    "Slovak", "Lithuanian", "Bulgarian", "Croatian", "Georgian",
    "Pashto", "Urdu", "Punjabi", "Gujarati", "Macedonian",
    "Slovenian", "Estonian", "Latvian", "Basque", "Catalan",
    "Irish", "Welsh", "Scottish Gaelic", "Icelandic", "Maltese",
    "Afrikaans", "Swahili", "Xhosa", "Zulu", "Yoruba",
    "Hausa", "Igbo", "Amharic", "Somali", "Twi",
    "Kurdish", "Armenian", "Azerbaijani", "Lao", "Khmer",
    "Burmese", "Mongolian", "Nepali", "Sinhala", "Marathi",
    "Telugu", "Kannada", "Malayalam", "Luganda", "Shona",
    "Chewa", "Maori", "Samoan", "Tongan", "Haitian Creole",
    "Quechua", "Aymara", "Navajo", "Cherokee", "Inuktitut",
    "Māori", "Tahitian", "Fijian", "Sundanese", "Javanese",
    "Basa Jawa", "Galician", "Corsican", "Tatar", "Uzbek",
    "Kazakh", "Tajik", "Turkmen", "Kyrgyz", "Uyghur"
]

# List of search terms
rotating_search_terms = [
    'Chinese', 'Mandarin', 'Cantonese', 'Taiwanese', 'Hokkien', 'Fujianese',
    'Hanyu', '汉语', '普通话', 'putonghua', '中文', 'heritage language', '继承语',
    '广东话', 'Taiwanese', 'Hokkien', '闽南语', '福建话', '福建语', '福建方言',
]

fixed_search_terms = "learn"

# Data collection
results = []

for term in rotating_search_terms:
    
    # query = f"{term} {fixed_search_terms}" # Dynamic search terms
    query = f"{term} language" # Fixed structure
    
    print(f"Searching for subreddits related to: {query}")
    
    for subreddit in reddit.subreddits.search(query, limit=10):
        try:
            # Extract subreddit info
            sub_name = subreddit.display_name
            sub_url = f"https://www.reddit.com{subreddit.url}"
            sub_subscribers = subreddit.subscribers
            sub_lang = "VERIFY"
            heritage = "heritage" in subreddit.title.lower() or "heritage" in subreddit.public_description.lower()
            learning_emphasis = "learn" in subreddit.title.lower() or "language" in subreddit.title.lower()
            description = subreddit.public_description
            
            # Determine focus language by scanning description
            matches = [lang for lang in languages if lang.lower() in description.lower()]

            if len(matches) == 1:
                sub_lang = matches[0]  # Single match
            elif len(matches) > 1:
                sub_lang = "Multiple"  # More than one match
            else:
                sub_lang = "Unknown"  # No match found


            # Get last post date
            last_post_time = datetime.fromtimestamp(
                next(subreddit.new(limit=1)).created_utc,
                tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S")

            # Append to results
            results.append({
                "Name": sub_name,
                "URL": sub_url,
                "Description": description,
                "Number of Subscribers": sub_subscribers,
                "Focus Language": sub_lang,
                "Learning Emphasis": "Yes" if learning_emphasis else "No",
                "Heritage Emphasis": "Yes" if heritage else "No",
                "Last Post Date/Time (UTC)": last_post_time
            })
            
            print(f"Found subreddit: {sub_name} - {sub_lang} - {sub_subscribers} subscribers")

        except Exception as e:
            print(f"Error processing {subreddit.display_name}: {e}")

# Convert to DataFrame
df = pd.DataFrame(results)
print(f"Total subreddits found: {len(df)}")
print(df.columns)
df.sort_values(by='Number of Subscribers', ascending=False, inplace=True)
# df.drop_duplicates(inplace=True)

# Export to CSV
# df.to_csv('reddit_search/search_results.csv', index=False)

print("Subreddit search complete. Data exported to language_subreddits.csv")