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

full_data = {}

for listing in raw_files:
    print(listing)
    if os.path.isfile(listing):
        file_date = re.match('.*([0-9]{8}).*\.csv$', listing).group(1)
        with open(listing) as csvfile:
            spamreader = csv.reader(csvfile)
            data = []
            for row in spamreader:
                data.append(dict(zip(header, row)))

            full_data[file_date] = data

with open(combined_file, 'w') as jsonFile:
    json.dump(full_data, jsonFile, indent=4)
