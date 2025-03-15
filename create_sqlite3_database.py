import sqlite3
import os
import csv
import re
import time
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('EmployeeDB.db')
c = conn.cursor()

# Add counter at the start of script, after database connection
files_processed = 0

# Add variables for timing
total_lines = 0
total_time = 0

# Create Person table
c.execute('''
CREATE TABLE IF NOT EXISTS Person (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    MostRecentTitle TEXT,
    MostRecentEmployer TEXT,
    MostRecentEntryDate DATE
)
''')

# Create indexes for Person table
print("Creating indexes...")
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_firstname
             ON Person(FirstName)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_lastname
             ON Person(LastName)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_fullname
             ON Person(FirstName, LastName)''')

# Create Salary table
c.execute('''
CREATE TABLE IF NOT EXISTS Salary (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PersonID INTEGER,
    Title TEXT,
    Employer TEXT,
    Salary REAL,
    Bonus REAL,
    TotalPay REAL,
    EntryDate DATE,
    SourceFile TEXT,
    FOREIGN KEY (PersonID) REFERENCES Person(ID)
)
''')

# Create indexes for Salary table
print("Creating Salary table indexes...")
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_personid
             ON Salary(PersonID)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_sourcefile
             ON Salary(SourceFile)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_employer
             ON Salary(Employer)''')

# Create DataFiles table
print("Creating DataFiles table...")
c.execute('''
CREATE TABLE IF NOT EXISTS DataFiles (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FileName TEXT NOT NULL,
    Rows INTEGER,
    FileDate DATE
)
''')

# Create index for DataFiles table
c.execute('''CREATE INDEX IF NOT EXISTS idx_datafiles_filename
             ON DataFiles(FileName)''')

# Commit the changes
conn.commit()

# Truncate existing tables
print("Clearing existing data...")
c.execute('DELETE FROM Salary')
c.execute('DELETE FROM Person')
c.execute('DELETE FROM DataFiles')
conn.commit()

# Function to parse date from filename
def parse_date_from_filename(filename):
    """Parse date from filename supporting multiple formats."""
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',  # mm-dd-yyyy or m-d-yyyy
        r'\d{8}',                   # mmddyyyy
        r'\d{1,2}\.\d{1,2}\.\d{4}'  # mm.dd.yyyy or m.d.yyyy
    ]
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group()
            try:
                if '-' in date_str:
                    return datetime.strptime(date_str, '%m-%d-%Y' if len(date_str.split('-')[0]) == 2 else '%m-%d-%Y').date()
                elif '.' in date_str:
                    return datetime.strptime(date_str, '%m.%d.%Y' if len(date_str.split('.')[0]) == 2 else '%m.%d.%Y').date()
                else:
                    return datetime.strptime(date_str, '%m%d%Y').date()
            except ValueError as e:
                print(f"Warning: Could not parse date from {date_str}: {e}")
                return None
    return None

# Add this helper function after the parse_date_from_filename function
def convert_pay_value(value_str):
    """Convert pay string to float, handling parentheses as negative numbers."""
    value_str = value_str.strip()
    is_negative = value_str.startswith('(') and value_str.endswith(')')
    # Remove $, commas, and parentheses
    clean_value = value_str.replace('$', '').replace(',', '').replace('(', '').replace(')', '')
    try:
        value = float(clean_value)
        return -value if is_negative else value
    except ValueError as e:
        raise ValueError(f"Could not convert {value_str} to number: {e}")

def is_header_row(row):
    """Check if row appears to be a header by looking for typical header terms and absence of numbers."""
    header_terms = ['name', 'employee', 'title', 'salary', 'pay', 'bonus', 'employer']
    has_header_terms = any(term in ' '.join(row).lower() for term in header_terms)
    has_numbers = any(any(char.isdigit() for char in cell) for cell in row)
    return has_header_terms and not has_numbers

# Process all CSV files in the raw_data directory
raw_data_dir = 'raw_data'
for filename in os.listdir(raw_data_dir):
    if filename.endswith('.csv'):
        file_path = os.path.join(raw_data_dir, filename)
        entry_date = parse_date_from_filename(filename)
        rows_processed = 0
        start_time = time.time()  # Start timing for this file

        print(f"\nProcessing file: {filename}")
        print(f"File Date: {entry_date}")

        try:
            # First try UTF-8 with BOM
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.reader(csvfile)
                first_row = next(reader)

                # Check if first row is a header
                if is_header_row(first_row):
                    print(f"Skipping header row in {filename}")
                else:
                    csvfile.seek(0)  # Reset to start if no header

                try:
                    line_count = 0  # Add counter for progress reporting
                    for row in reader:
                        line_count += 1
                        if line_count % 10000 == 0:
                            print(f"Processing line {line_count} in {filename}")

                        # Skip empty rows or if this is another header-like row
                        if not row or all(cell.strip() == '' for cell in row) or is_header_row(row):
                            continue

                        # Clean any potential invalid characters from strings
                        cleaned_row = []
                        for cell in row:
                            try:
                                # Attempt to encode and decode to catch invalid characters
                                cleaned_cell = cell.encode('utf-8', 'ignore').decode('utf-8')
                                if cleaned_cell != cell:
                                    print(f"Warning: Invalid characters removed from cell in {filename}, row {reader.line_num}")
                                cleaned_row.append(cleaned_cell)
                            except UnicodeError as e:
                                print(f"Warning: Unicode error in {filename}, row {reader.line_num}: {e}")
                                cleaned_row.append('')

                        row = cleaned_row

                        try:
                            first_name = row[0].strip() if row[0].strip() else 'Unknown'
                            last_name = row[1].strip() if row[1].strip() else 'Unknown'
                            title = row[2].strip() if row[2].strip() else 'Unknown'
                            employer = row[3].strip() if row[3].strip() else 'Unknown'

                            # Handle different pay formats
                            if len(row) >= 5:
                                # Remove any trailing commas and empty cells
                                pay_values = [cell.strip() for cell in row[4:] if cell.strip() and not cell.strip().endswith(',')]

                                if len(pay_values) == 0:
                                    print(f"No valid pay data found for {first_name} {last_name}")
                                    continue

                                if len(pay_values) == 1:
                                    # Single value case - treat as total pay
                                    total_pay = convert_pay_value(pay_values[0])
                                    salary = bonus = None
                                else:
                                    # Multiple values case
                                    salary = convert_pay_value(pay_values[0])
                                    if len(pay_values) > 2:
                                        bonus = convert_pay_value(pay_values[1])
                                        total_pay = convert_pay_value(pay_values[2])
                                    else:
                                        bonus = None
                                        total_pay = convert_pay_value(pay_values[-1])
                            else:
                                print(f"Insufficient data columns for {first_name} {last_name}")
                                continue

                        except (ValueError, IndexError) as e:
                            print(f"Error processing row: {row}. Error: {e}")
                            continue

                        # Check if person already exists
                        c.execute('SELECT ID FROM Person WHERE FirstName = ? AND LastName = ?', (first_name, last_name))
                        person = c.fetchone()

                        if person:
                            person_id = person[0]
                        else:
                            # Insert new person
                            c.execute('''
                            INSERT INTO Person (FirstName, LastName, MostRecentTitle, MostRecentEmployer, MostRecentEntryDate)
                            VALUES (?, ?, ?, ?, ?)''', (first_name, last_name, title, employer, entry_date))
                            person_id = c.lastrowid

                        # Insert salary record
                        c.execute('''
                        INSERT INTO Salary (PersonID, Title, Employer, Salary, Bonus, TotalPay, EntryDate, SourceFile)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (person_id, title, employer, salary, bonus, total_pay, entry_date, filename))

                        # Update person's most recent details
                        c.execute('''
                        UPDATE Person
                        SET MostRecentTitle = ?, MostRecentEmployer = ?, MostRecentEntryDate = ?
                        WHERE ID = ?''', (title, employer, entry_date, person_id))

                        # After successful database updates, increment counter
                        rows_processed += 1

                except UnicodeDecodeError as e:
                    print(f"Warning: Unicode decode error in {filename}: {e}")
                    continue

        except UnicodeDecodeError as e:
            print(f"Error: Unable to process {filename} with UTF-8 encoding: {e}")
            try:
                # Fallback to Latin-1 encoding
                print(f"Attempting to read {filename} with Latin-1 encoding")
                with open(file_path, 'r', encoding='latin-1', newline='') as csvfile:
                    # ... same processing code as above ...
                    pass
            except Exception as e:
                print(f"Error: Failed to process {filename} with Latin-1 encoding: {e}")
                continue

        # After file is processed, calculate and display metrics
        end_time = time.time()
        processing_time = end_time - start_time
        lines_per_second = rows_processed / processing_time if processing_time > 0 else 0

        print(f"\nFile Processing Complete:")
        print(f"File: {filename}")
        print(f"Rows processed: {rows_processed}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Performance: {lines_per_second:.2f} lines/second")

        # Store file information
        c.execute('''
        INSERT INTO DataFiles (FileName, Rows, FileDate)
        VALUES (?, ?, ?)
        ''', (filename, rows_processed, entry_date))

        # Update totals
        total_lines += rows_processed
        total_time += processing_time
        files_processed += 1

        # Commit changes for each file
        conn.commit()

# Before closing connection, add summary queries
print("\nProcessing Summary:")
print("-----------------")
print(f"Files Processed: {files_processed}")
print(f"Total Lines Processed: {total_lines}")
print(f"Total Processing Time: {total_time:.2f} seconds")
print(f"Overall Performance: {(total_lines/total_time if total_time > 0 else 0):.2f} lines/second")

# Get total number of people
c.execute('SELECT COUNT(*) FROM Person')
total_people = c.fetchone()[0]

# Get total number of salary records
c.execute('SELECT COUNT(*) FROM Salary')
total_salaries = c.fetchone()[0]

print(f"Total People: {total_people}")
print(f"Total Salary Records: {total_salaries}")

print("\nUpdating Person records with most recent information...")
c.execute('''
UPDATE Person
SET
    MostRecentTitle = (
        SELECT s.Title
        FROM Salary s
        WHERE s.PersonID = Person.ID
        ORDER BY s.EntryDate DESC
        LIMIT 1
    ),
    MostRecentEmployer = (
        SELECT s.Employer
        FROM Salary s
        WHERE s.PersonID = Person.ID
        ORDER BY s.EntryDate DESC
        LIMIT 1
    ),
    MostRecentEntryDate = (
        SELECT s.EntryDate
        FROM Salary s
        WHERE s.PersonID = Person.ID
        ORDER BY s.EntryDate DESC
        LIMIT 1
    )
''')

# Commit the final updates
conn.commit()

print(f"Updated {c.rowcount} Person records with most recent information")

# Close the connection
conn.close()
print('\nDatabase created successfully.')
