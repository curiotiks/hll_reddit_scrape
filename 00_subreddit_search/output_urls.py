import pandas as pd
import json

# Load the metadata and selection table
filepath = '../meta_data.json'
selection_table = pd.read_csv('summary_hand_filtered.csv')
combined_data = pd.read_csv('combined_output.csv').drop_duplicates()

with open(filepath, 'r') as file: 
    meta_data = json.load(file)

# Filter the selection table based on the 'Include' column
selection_table = selection_table[selection_table['Include'] == 1]['Name']
combined_data = combined_data[combined_data['Name'].isin(selection_table)].reset_index()

# Add list of URLs to metadata
meta_data['sub_urls'] = combined_data['URL'].tolist()

with open(filepath, 'w') as file:
    json.dump(meta_data, file, indent=4)
