import sqlite3
import os
import csv
import re
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('EmployeeDB.db')
c = conn.cursor()

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
    FOREIGN KEY (PersonID) REFERENCES Person(ID)
)
''')

# Commit the changes
conn.commit()

# Truncate existing tables
print("Clearing existing data...")
c.execute('DELETE FROM Salary')
c.execute('DELETE FROM Person')
conn.commit()

# Function to parse date from filename
def parse_date_from_filename(filename):
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',  # mm-dd-yyyy or m-d-yyyy
        r'\d{8}'                   # mmddyyyy
    ]
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group()
            if '-' in date_str:
                return datetime.strptime(date_str, '%m-%d-%Y' if len(date_str.split('-')[0]) == 2 else '%m-%d-%Y').date()
            else:
                return datetime.strptime(date_str, '%m%d%Y').date()
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

# Process all CSV files in the raw_data directory
raw_data_dir = 'raw_data'
for filename in os.listdir(raw_data_dir):
    if filename.endswith('.csv'):
        file_path = os.path.join(raw_data_dir, filename)
        entry_date = parse_date_from_filename(filename)
        rows_processed = 0

        print(f"\nProcessing file: {filename}")
        print(f"Data date: {entry_date}")

        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            if not header[0].strip().lower().startswith('first'):
                csvfile.seek(0)
                header = None

            for row in reader:
                # Skip empty rows
                if not row or all(cell.strip() == '' for cell in row):
                    continue

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
                INSERT INTO Salary (PersonID, Title, Employer, Salary, Bonus, TotalPay, EntryDate)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (person_id, title, employer, salary, bonus, total_pay, entry_date))

                # Update person's most recent details
                c.execute('''
                UPDATE Person
                SET MostRecentTitle = ?, MostRecentEmployer = ?, MostRecentEntryDate = ?
                WHERE ID = ?''', (title, employer, entry_date, person_id))

                # After successful database updates, increment counter
                rows_processed += 1

        # Commit changes for each file
        conn.commit()
        print(f"Processed {filename}: {rows_processed} rows")

# Close the connection
conn.close()
print('Database created successfully.')
