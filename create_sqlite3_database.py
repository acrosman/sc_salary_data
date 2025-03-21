import sqlite3
import os
import csv
import re
import time
from datetime import datetime

# Configuration and tracking variables
raw_data_dir = 'raw_data'
files_processed = 0
total_lines = 0
total_time = 0
database_name = 'EmployeeDB.db'

# Database initialization and schema creation
conn = sqlite3.connect(database_name)
c = conn.cursor()

# Person table stores unique individuals and their most recent employment details
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

# Indexes to optimize person lookups by name
print("Creating indexes...")
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_firstname
             ON Person(FirstName)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_lastname
             ON Person(LastName)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_person_fullname
             ON Person(FirstName, LastName)''')

# Salary table stores all salary records with foreign key to Person
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
    LineNumber INTEGER,
    FOREIGN KEY (PersonID) REFERENCES Person(ID)
)
''')

# Indexes to optimize salary record lookups and joins
print("Creating Salary table indexes...")
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_personid
             ON Salary(PersonID)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_sourcefile
             ON Salary(SourceFile)''')
c.execute('''CREATE INDEX IF NOT EXISTS idx_salary_employer
             ON Salary(Employer)''')

# DataFiles table tracks processed files and their statistics
print("Creating DataFiles table...")
c.execute('''
CREATE TABLE IF NOT EXISTS DataFiles (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FileName TEXT NOT NULL,
    Rows INTEGER,
    FileDate DATE,
    HasHeader BOOLEAN DEFAULT 0
)
''')

# Create index for DataFiles table
c.execute('''CREATE INDEX IF NOT EXISTS idx_datafiles_filename
             ON DataFiles(FileName)''')

# Commit the changes
conn.commit()

# Reset database for fresh import
print("Clearing existing data...")
c.execute('DELETE FROM Salary')
c.execute('DELETE FROM Person')
c.execute('DELETE FROM DataFiles')
c.execute('DELETE FROM SQLITE_SEQUENCE WHERE name IN ("Salary", "Person", "DataFiles")')  # Reset autoincrement counters
conn.commit()

# Helper function for parsing dates from filenames
def parse_date_from_filename(filename):
    """Parse date from filename supporting multiple formats:
       - mm-dd-yyyy or m-d-yyyy
       - mmddyyyy
       - mm.dd.yyyy or m.d.yyyy
       - mm-yyyy (uses 1st as day)
       - mm.yyyy (uses 1st as day)
    """
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',  # mm-dd-yyyy or m-d-yyyy
        r'\d{8}',                   # mmddyyyy
        r'\d{1,2}\.\d{1,2}\.\d{4}',  # mm.dd.yyyy or m.d.yyyy
        r'\d{1,2}-\d{4}',           # mm-yyyy
        r'\d{1,2}\.\d{4}'           # mm.yyyy
    ]
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group()
            try:
                if '-' in date_str:
                    if len(date_str.split('-')) == 2:  # mm-yyyy format
                        month, year = date_str.split('-')
                        return datetime(int(year), int(month), 1).date()
                    return datetime.strptime(date_str, '%m-%d-%Y' if len(date_str.split('-')[0]) == 2 else '%m-%d-%Y').date()
                elif '.' in date_str:
                    if len(date_str.split('.')) == 2:  # mm.yyyy format
                        month, year = date_str.split('.')
                        return datetime(int(year), int(month), 1).date()
                    return datetime.strptime(date_str, '%m.%d.%Y' if len(date_str.split('.')[0]) == 2 else '%m.%d.%Y').date()
                else:
                    return datetime.strptime(date_str, '%m%d%Y').date()
            except ValueError as e:
                print(f"Warning: Could not parse date from {date_str}: {e}")
                return None
    return None

# Helper function for converting pay values to floats
def convert_pay_value(value_str):
    """Convert pay string to float, handling:
       - Dollar signs and commas
       - Parentheses for negative numbers
       - Empty or invalid values
    """
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
    """Detect header rows by checking for:
       - Common header terms
       - Absence of numeric values
       - Standard header patterns
    """
    header_terms = ['name', 'employee', 'title', 'salary', 'pay', 'bonus', 'employer']
    has_header_terms = any(term in ' '.join(row).lower() for term in header_terms)
    has_numbers = any(any(char.isdigit() for char in cell) for cell in row)
    return has_header_terms and not has_numbers

def process_pay_values(pay_values, first_name, last_name):
    """Process pay values from CSV row and return salary, bonus, and total pay."""
    if len(pay_values) == 0:
        print(f"No valid pay data found for {first_name} {last_name}")
        return None, None, None

    if len(pay_values) == 1:
        # Single value case - treat as total pay
        return None, None, convert_pay_value(pay_values[0])

    # Multiple values case
    salary = convert_pay_value(pay_values[0])
    if len(pay_values) > 2:
        bonus = convert_pay_value(pay_values[1])
        total_pay = convert_pay_value(pay_values[2])
    else:
        bonus = None
        total_pay = convert_pay_value(pay_values[-1])

    return salary, bonus, total_pay

def process_row(row, filename, reader_line_num):
    """Process a single row from the CSV file and return the processed values."""
    # Clean any potential invalid characters from strings
    cleaned_row = []
    for cell in row:
        try:
            cleaned_cell = cell.encode('utf-8', 'ignore').decode('utf-8')
            if cleaned_cell != cell:
                print(f"Warning: Invalid characters removed from cell in {filename}, row {reader_line_num}")
            cleaned_row.append(cleaned_cell)
        except UnicodeError as e:
            print(f"Warning: Unicode error in {filename}, row {reader_line_num}: {e}")
            cleaned_row.append('')

    row = cleaned_row

    # Extract basic information
    last_name = row[0].strip() if row[0].strip() else 'Unknown'
    first_name = row[1].strip() if row[1].strip() else 'Unknown'
    employer = row[2].strip() if row[2].strip() else 'Unknown'
    title = row[3].strip() if row[3].strip() else 'Unknown'

    # Handle pay values
    if len(row) < 5:
        print(f"Insufficient data columns for {first_name} {last_name}")
        return None

    # Remove any trailing commas and empty cells
    pay_values = [cell.strip() for cell in row[4:] if cell.strip() and not cell.strip().endswith(',')]
    salary, bonus, total_pay = process_pay_values(pay_values, first_name, last_name)

    if total_pay is None:
        return None

    return {
        'first_name': first_name,
        'last_name': last_name,
        'employer': employer,
        'title': title,
        'salary': salary,
        'bonus': bonus,
        'total_pay': total_pay,
        'line_number': reader_line_num
    }

# Main processing loop for all CSV files
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

                # Check if first row is a header and store result
                has_header = is_header_row(first_row)
                if has_header:
                    print(f"Skipping header row in {filename}")
                else:
                    csvfile.seek(0)  # Reset to start if no header

                try:
                    line_count = 0
                    for row in reader:
                        line_count += 1
                        if line_count % 10000 == 0:
                            print(f"Processing line {line_count} in {filename}")

                        # Skip empty rows or if this is another header-like row
                        if not row or all(cell.strip() == '' for cell in row) or (has_header and is_header_row(row)):
                            continue

                        # Process the row
                        processed_data = process_row(row, filename, reader.line_num)
                        if processed_data is None:
                            continue

                        # Check if person already exists
                        c.execute('SELECT ID FROM Person WHERE FirstName = ? AND LastName = ?',
                                (processed_data['first_name'], processed_data['last_name']))
                        person = c.fetchone()

                        if person:
                            person_id = person[0]
                        else:
                            # Insert new person
                            c.execute('''
                            INSERT INTO Person (FirstName, LastName, MostRecentTitle, MostRecentEmployer, MostRecentEntryDate)
                            VALUES (?, ?, ?, ?, ?)''',
                            (processed_data['first_name'], processed_data['last_name'],
                             processed_data['title'], processed_data['employer'], entry_date))
                            person_id = c.lastrowid

                        # Insert salary record
                        c.execute('''
                        INSERT INTO Salary (PersonID, Title, Employer, Salary, Bonus, TotalPay, EntryDate, SourceFile, LineNumber)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (person_id, processed_data['title'], processed_data['employer'],
                         processed_data['salary'], processed_data['bonus'], processed_data['total_pay'],
                         entry_date, filename, processed_data['line_number']))

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
        INSERT INTO DataFiles (FileName, Rows, FileDate, HasHeader)
        VALUES (?, ?, ?, ?)
        ''', (filename, rows_processed, entry_date, 1 if has_header else 0))

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

# Update each person's record with their most recent employment information from all salary entries
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
