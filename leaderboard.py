from datetime import datetime, timedelta
from typing import List, Tuple
from calendar import monthrange
from database import get_database_connection, get_database_cursor

connection = get_database_connection()
cursor = get_database_cursor(connection)

def time_online(data: str, start_date: str, end_date: str) -> timedelta:
    start_date = datetime.fromisoformat(start_date).date()
    end_date = datetime.fromisoformat(end_date).date()

    events = [event.split(': ') for event in data.split(',')]
    events = [(status, datetime.fromisoformat(timestamp)) for status, timestamp in events]

    online_time = timedelta()
    online_start = None

    for status, timestamp in events:
        if status == "online" and start_date <= timestamp.date() <= end_date:
            online_start = timestamp
        elif status == "offline" and online_start is not None:
            online_time += timestamp - online_start
            online_start = None

    return online_time

def get_user_logs() -> List[Tuple[int, str, str]]:
    connection = get_database_connection()
    cursor = get_database_cursor(connection)
    cursor.execute("SELECT user_id, username, logs FROM user_logs")
    user_logs = cursor.fetchall()
    connection.close()
    return user_logs

def create_leaderboard_array(user_online_times: List[Tuple[str, timedelta]], limit) -> List[Tuple[int, str, timedelta]]:
    leaderboard_array = []
    for index, (username, online_time) in enumerate(user_online_times[:limit], start=1):
        leaderboard_array.append((index, username, online_time))
    return leaderboard_array

def show_leaderboard(limit):
    today = datetime.today()
    current_month = today.month
    start_date = today.replace(day=1, month=current_month).strftime('%Y-%m-%d')
    end_date = today.replace(day=monthrange(today.year, current_month)[1], month=current_month).strftime('%Y-%m-%d')

    user_logs = get_user_logs()

    user_online_times = [(username, time_online(logs, start_date, end_date)) for user_id, username, logs in user_logs]

    user_online_times.sort(key=lambda x: x[1], reverse=True)

    leaderboard_array = create_leaderboard_array(user_online_times, limit)

    return leaderboard_array

leaderboard = show_leaderboard(15)
#print(leaderboard)