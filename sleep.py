import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
from discord import app_commands
from discord.ext import commands
import pytz
import os
from dotenv import load_dotenv

from baby import plot_user



load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

tz = pytz.timezone('Europe/Vilnius')

# create a SQLite database
connection = sqlite3.connect('log_data.db')
cursor = connection.cursor()


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
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                user_logs = user_logs[0] + f",offline: {formatted_time}"
                cursor.execute("UPDATE user_logs SET logs = ? WHERE user_id = ?", (user_logs, user_id))
                connection.commit()
                print(f"{username} went offline")
            else:
                pass
        elif before.status == discord.Status.offline and after.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
            user_id = str(after.id)
            username = after.name
            user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user_id,)).fetchone()
            if user_logs:
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                user_logs = user_logs[0] + f",online: {formatted_time}"
                cursor.execute("UPDATE user_logs SET logs = ? WHERE user_id = ?", (user_logs, user_id))
                connection.commit()
                print(f"user {username} came online")
            else:
                # if user logs do not exist, create new row for the user
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                user_logs = f"online: {formatted_time}"
                cursor.execute("INSERT INTO user_logs (user_id, username, logs) VALUES (?, ?, ?)", (user_id, username, user_logs))
                connection.commit()
                print(f"user {username} came online")




@bot.tree.command(name="schedule")
async def greet(interaction: discord.Interaction, user: discord.Member):
    #if command is used in channel with id 888888888888888888
    if interaction.channel_id == 1062174423685287976:
        await interaction.response.defer() 
        #run renkochart with userid as input
        try:

            file = plot_user(user.id)
            await interaction.followup.send(file=file)
            #log
            print(f"User {user.name} requested chart for {user.name} in {interaction.channel.name}")

        except:

            await interaction.followup.send("No data found", ephemeral=True)
     
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#bot run
bot.run(TOKEN)
