
from requests_html import HTMLSession
import os.path
import sys
from urllib.parse import unquote

script_dir = sys.path[0]
admin_site = "https://www.admin.sc.gov"
salary_path = "/transparency/state-salaries"
storage_dir = os.path.join(script_dir, "raw_data")

session = HTMLSession()
r = session.get(admin_site + salary_path)

csv_link = r.html.find('a:contains(\'Download State Salaries\')', first=True)
csv_path = csv_link.attrs['href']

file_name = unquote(os.path.basename(csv_path))

local_file = os.path.join(storage_dir, file_name)
if not os.path.exists(local_file):
    csv_r = session.get(admin_site + csv_path)
    data = csv_r.content.decode(csv_r.encoding).encode('utf8')
    new_file = open(local_file, "wb")
    new_file.write(data)
    new_file.close()
    print("New SC Salary data file: " + file_name)
