import discord
from discord.ext import commands
import sqlite3
from datetime import datetime


TOKEN = 'MTA4NDM2NTgwODc4NTk1Mjg0OQ.GKvuXg.8h26f_K1z6YifcatvfwOkLQhYTFZLflPxueFhU'

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# create a SQLite database
connection = sqlite3.connect('log_data.db')
cursor = connection.cursor()

# create a table to store user logs
cursor.execute('''CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                logs TEXT NOT NULL)''')
connection.commit()


#on ready event
@bot.event
async def on_ready():
    print("Bot is ready")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    #display all servers where bot is in
    print("####################")
    print("Servers: \n")
    for guild in bot.guilds:
        print(guild.name)
    print("####################")


# on user status change
@bot.event
async def on_presence_update(before, after):
    # check if user goes offline or comes back online
    if before.status != after.status:
        if before.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd] and after.status == discord.Status.offline:
            user_id = str(after.id)
            username = after.name
            user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user_id,)).fetchone()
            if user_logs:
                # if user logs already exist, append new log to the logs
                user_logs = user_logs[0] + f",offline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                cursor.execute("UPDATE user_logs SET logs = ? WHERE user_id = ?", (user_logs, user_id))
                connection.commit()
            else:
                # do nothing
                pass
        elif before.status == discord.Status.offline and after.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
            user_id = str(after.id)
            username = after.name
            user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user_id,)).fetchone()
            if user_logs:
                # if user logs already exist, append new log to the logs
                user_logs = user_logs[0] + f",online: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                cursor.execute("UPDATE user_logs SET logs = ? WHERE user_id = ?", (user_logs, user_id))
                connection.commit()
            else:
                # if user logs do not exist, create new row for the user
                user_logs = f"online: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                cursor.execute("INSERT INTO user_logs (user_id, username, logs) VALUES (?, ?, ?)", (user_id, username, user_logs))
                connection.commit()



#bot run
bot.run(TOKEN)
