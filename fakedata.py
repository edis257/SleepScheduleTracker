import sqlite3

# create a SQLite database
connection = sqlite3.connect('log_data.db')
cursor = connection.cursor()

#fake data
user_id = "302050872383242240"
username = "test"
logs = "online: 2023-03-11 08:08:22,offline: 2023-03-11 08:09:22,online: 2023-03-12 13:04:38,offline: 2023-03-12 13:34:38"

#insert fake data
cursor.execute("INSERT INTO user_logs (user_id, username, logs) VALUES (?, ?, ?)", (user_id, username, logs))
connection.commit()

