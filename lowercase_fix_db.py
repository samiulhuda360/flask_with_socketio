import sqlite3

# Connect to the database
connection = sqlite3.connect('sites_data.db')
cursor = connection.cursor()

# Update all sitename values to lowercase
cursor.execute('UPDATE sites SET sitename = LOWER(sitename)')
connection.commit()

# Verify the changes
cursor.execute('SELECT * FROM sites')
rows = cursor.fetchall()
for row in rows:
    print(row)  # Print all rows to confirm sitenames are in lowercase

# Close the connection
connection.close()