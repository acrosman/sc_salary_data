from requests_html import HTMLSession
from datetime import datetime
import os.path
import sys
import glob
import filecmp
import re

script_dir = sys.path[0]
now = datetime.now()
admin_site = "https://www.admin.sc.gov"
file_path = "/download/ohr/State%20Employees%20by%20County.pdf"
local_file_name = "State_Employees_By_Agency_" + now.strftime("%Y%m%d")
storage_dir = os.path.join(script_dir, "raw_data")

# == Get the current file ==
session = HTMLSession()
r = session.get(admin_site + file_path)
# Add the extension (could be smarter)
file_extension = r.headers.get('Content-Type').split('/')[1]
local_file_name += '.' + file_extension

local_file = os.path.join(storage_dir, local_file_name)
if not os.path.exists(local_file):
    new_file = open(local_file, "wb")
    new_file.write(r.content)
    new_file.close()
    print("New SC Employee count data file: " + local_file)
else:
    print("File " + local_file + " exists")

# == Check against previous file ==
newest = {'date': 0, 'file': ''}
current_files = glob.iglob(storage_dir + '/*.' + file_extension)
for listing in current_files:
    print(listing)
    if os.path.isfile(listing) and listing != local_file:
        file_date = int(re.match('.*([0-9]{8}).*\.' + file_extension + '$',
                                  listing).group(1))
        if newest['date'] < file_date:
            newest = {'date': file_date, 'file': listing}

# If the files are the same, delete the new one.
if newest['date'] > 0:
    if filecmp.cmp(newest['file'], local_file):
        os.remove(local_file)
