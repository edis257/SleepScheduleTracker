import sqlite3
import os
from dotenv import load_dotenv

def get_database_connection():
    load_dotenv()
    database_path = os.getenv('DATABASE_PATH')
    connection = sqlite3.connect(database_path)
    return connection

def get_database_cursor(connection):
    cursor = connection.cursor()
    return cursor