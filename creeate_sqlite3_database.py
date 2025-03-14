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

# Process all CSV files in the raw_data directory
raw_data_dir = 'raw_data'
for filename in os.listdir(raw_data_dir):
    if filename.endswith('.csv'):
        file_path = os.path.join(raw_data_dir, filename)
        entry_date = parse_date_from_filename(filename)

        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            if not header[0].strip().lower().startswith('first'):
                csvfile.seek(0)
                header = None

            for row in reader:
                first_name = row[0].strip()
                last_name = row[1].strip()
                title = row[2].strip()
                employer = row[3].strip()

                try:
                    # Detect column count to handle total pay only case
                    if len(row) == 5:
                        total_pay = float(row[4].strip().replace('$', '').replace(',', ''))
                        salary = bonus = None
                    else:
                        salary = float(row[4].strip().replace('$', '').replace(',', ''))
                        bonus = float(row[5].strip().replace('$', '').replace(',', ''))
                        total_pay = float(row[6].strip().replace('$', '').replace(',', ''))
                except ValueError as e:
                    print(f"Error converting data for row: {row}. Error: {e}")
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

        # Commit changes for each file
        conn.commit()

# Close the connection
conn.close()
print('Database created successfully.')
