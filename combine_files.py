import csv
import sys
import os.path
import glob
import re
import json

script_dir = sys.path[0]
data_dir = os.path.join(script_dir, 'raw_data')
combined_file = os.path.join(script_dir, 'processed.json')
header = [
    'Last Name', 'First Name', 'Agency', 'Job Title',
    'Total Compensation', 'Bonuses'
]
raw_files = glob.iglob(data_dir + '/*.csv')


def cleanRow(row):
    new_row = []
    for cell in row:
        cell = cell.strip().title()
        if cell[:1] == '$':
            cell = cell[1:].replace(',', '')
        new_row.append(cell)

    return new_row


full_data = {}

for listing in raw_files:
    print(listing)
    if os.path.isfile(listing):
        # Updated regex to match 'M.YYYY' format in the filename
        match = re.match(r'.*([0-9]{1,2}\.[0-9]{4}).*\.csv$', listing)
        
        # Check if match exists before accessing group(1) to avoid AttributeError
        if match:  # Updated conditional check to prevent errors
            file_date = match.group(1)
            with open(listing) as csvfile:
                spamreader = csv.reader(csvfile)
                data = []
                for row in spamreader:
                    row = cleanRow(row)
                    data.append(dict(zip(header, row)))

                full_data[file_date] = data
        else:
            print(f"Warning: No valid date found in filename '{listing}'")  # Added warning message

with open(combined_file, 'w') as jsonFile:
    json.dump(full_data, jsonFile, indent=4)
