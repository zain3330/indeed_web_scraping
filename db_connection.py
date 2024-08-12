import mysql.connector

def connect_to_database():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345',
        database='web_scraping'
    )
    return connection


