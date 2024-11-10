import sqlite3

def reset_database(db_path):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Delete all rows from each table
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip sqlite_sequence table (auto-increment data)
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"All data deleted from table: {table_name}")

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print("Database has been reset successfully, schema remains intact.")
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

# Path to your SQLite database
db_path = '/var/www/flask_with_socketio/sites_data.db'

# Call the function to reset the database
reset_database(db_path)
