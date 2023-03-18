import sqlite3

connection = sqlite3.connect('log_data.db')
cursor = connection.cursor()

# create a table to store user logs
cursor.execute('''CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                logs TEXT NOT NULL)''')
connection.commit()

# create a table to store user activity logs
cursor.execute('''CREATE TABLE IF NOT EXISTS user_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                logs TEXT NOT NULL)''')
connection.commit()

cursor.execute("CREATE TABLE IF NOT EXISTS ignored_users (user_id TEXT PRIMARY KEY)")
connection.commit()
