# Salary Data Explorations

This is a project to explore the SC Salary data. The provided through the state's accountability portal: https://www.admin.sc.gov/accountability-portal.

There are two sets of files currently in the `raw_data` directory: salary csv files, and state employee counts by agency.

Files before July 2019 were pulled from Archive.org's copy of the site. There are some points in which the CSV file links appear to have been broken and so some files may be missing.

Please also note that the SC State Accountablitity Portal provides a careful descripion of the limits of this information, including agencies not included, and agencies not providing full details about all compensation. To fully understand the limits of accuracy please review that source for details.

## Data Files

There are two sets of data provided in this project currently: Salary data as disclosed by the state government for people making more than $50,000 a year.  The second is a count of employees by agency as provided by the state. _They should not match_ as the state does not include a disclaimer saying it is just counts of employees making more than 50,000, and is included here on the theory that it will make it eaiser to create rough estimates about how these more poorly paid employees effect calculations of averages.

## Scripts

This project provides a few simple scripts to help aquire files over time and clean them up.

### get_salary_data.py

`get_salary_data.py` is a Python 3 script that checks for a few version of the salary data file on the admin.sc.gov and adds it to the `raw_data` directory when a new one is found. This script is designed as a daily cron job and assumes the page layout and links use the same markup they have used since 2015 (one day this will be an invalid assumption).

### combine_files.py

`combine_files.py` takes all `.csv` files in the `raw_data` directory and combines them into a the `processed.json` file to provide the full historic data set.

### get_emp_data.py

`get_emp_data.py` downloads the employee count reports provided currently in PDF form. It is designed as a daily cron job, and assumes the link doesn't change and that they do not switch to CSV (which could cause naming conflicts with the salary data).

# Licensing

As the actual salary information here is SC State government provided data it is in the public domain. The included License only applies to other material in this project. All content in the `raw_data` directory is public domain. File content there is unaltered from the source except the file name.
