# Salary Data Explorations

This is a project to explore the SC Salary data that is provided through [the state's Tranparency Portal](https://www.admin.sc.gov/transparency/transparency-portal.)

There are two sets of files currently in the `raw_data` directory: salary CSV files and state employee counts by agency. Files before July 2019, were pulled from Archive.org's copy of the site and there are points at which the CSV file links appear to have been broken so some files may be missing. Please also note that the SC State Accountablitity Portal provides a careful descripion of the limitations of this information, which includes agencies not being included or not providing full details about all compensation, so review that source to fully understand the accuracy limits of this data.

## Data Files

There are two sets of data provided in this project currently: Salary data as disclosed by the state government for people making more than $50,000 a year and a count of employees by agency as provided by the state. These two data sets should not match as the state does not include a disclaimer stating that only employees making more than $50,000 are included in the count. The state's data is included here as it should, in theory, make it easier to create rough estimates about how these lower paid employees effect the calculation of averages.

## Scripts

This project provides a few simple scripts to help aquire files over time and clean them up.

### get_salary_data.py

Checks for a new version of the salary data file on the admin.sc.gov site and adds it to the `raw_data` directory when one is found. This script is designed as a daily cron job and assumes the page layout and links use the same markup they have used since 2015 (one day this will be an invalid assumption).

### combine_files.py

Takes all `.csv` files in the `raw_data` directory and combines them into the `processed.json` file in order to provide the full historic data set.

### get_emp_data.py

Downloads the employee count reports provided in PDF format (currently). It is designed as a daily cron job, and assumes the link doesn't change and that they do not switch to CSV (which could cause naming conflicts with the salary data).

# Licensing

The included License only applies to other material in this project as the salary information (provided by the SC State government) and the content in the `raw_data` directory (which is unaltered from the source except the filename) are both public domain.
