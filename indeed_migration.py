# migration.py

# import connection
from db_connection import connect_to_database

def create_table(connection):
    # cursor is used to execute sql queries
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indeed (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            company_location VARCHAR(255),
            salary VARCHAR(255),
            job_type VARCHAR(255),
            description TEXT,
            posted_at VARCHAR(255)
        );
    ''')
    #  Saves all the changes you made to the database.
    connection.commit()
    # Closes the cursor
    cursor.close()


def run_migrations():
    connection = None

    try:
        connection = connect_to_database()
        create_table(connection)
    # code inside the finally block runs regardless of whether an error occurred in the try block or not.
    finally:
        if connection:
            connection.close()

# If this script is being run directly by itself, then do the following.
if __name__ == "__main__":
    run_migrations()

