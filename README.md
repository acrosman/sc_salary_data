# South Carolina State Employee Salary Data

This is a project to explore the SC Salary data that is provided through [the state's Transparency Portal](https://www.admin.sc.gov/transparency/transparency-portal).

There are two sets of files currently in the `raw_data` directory: salary CSV files and PDF files of state employee counts by agency. Files before July 2019, were pulled from Archive.org's copy of the site and there are points at which the CSV file links appear to have been broken so some files may be missing. The data included goes back to 2015.

Please also note, that the SC State Accountability Portal provides a careful description of the limitations of this information; that description includes agencies not being included those which do not provide full details about all compensation. Review that source fully to understand the accuracy limits of this data.

## Data Files

Salary data as disclosed by the South Carolina state government for state employees making more than $50,000 a year and a count of employees by agency as provided by the state. These two data sets do not match as the employee counts include people making less than $50,000.

The state's data is included here as it should, in theory, make it easier to create rough estimates about how these lower paid employees affect the calculation of averages.

## Scripts

This project provides a few simple scripts to help acquire files over time and clean them up.

### get_salary_data.py

This script checks for a new version of the salary data file on the admin.sc.gov site and adds it to the `raw_data` directory if one is found. This script is designed as a daily cron job and is based on the page layout and structure at it's last revision.

### get_emp_data.py

Downloads the employee count reports provided in PDF format. It is designed as a daily cron job and assumes the link doesn't change and that they do not switch to CSV (which could cause naming conflicts with the salary data).

### combine_files.py

Takes all `.csv` files in the `raw_data` directory and combines them into a `processed.json` file in order to provide the full historic data set. The project includes a version of that file, but it stops in 2019 (due to file size limitations of Github).

### create_sqlite3_database.py

Creates a SQLite3 database from all the csv data. This script was written with significant support of copilot (in part to test the status of how well copilot works at the time of writing). Over time it may, or may not, be edited by hand and by copilot.

# Licensing

The included License only applies to scripts and text files in this project. The salary information is provided by the SC State government and so the content in the `raw_data` directory is both public domain. All data files are provided with their original content with just file name changes from the originals.
