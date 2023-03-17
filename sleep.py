import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
from discord import app_commands
from discord.ext import commands
import pytz
import os
from dotenv import load_dotenv
from discord import Spotify


from baby import plot_user
from functions import get_last_n_records


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
interaction_channel = os.getenv('INTERACTION_CHANNEL')

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




     #if activity changes
    if before.activity != after.activity:
        if after and after.activity and after.activity.name:
            #log activity to database
            user_id = str(after.id)
            username = after.name
            user_logs = cursor.execute("SELECT logs FROM user_activity_logs WHERE user_id = ?", (user_id,)).fetchone()
            if user_logs:                    
                    current_time = datetime.now(tz)
                    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    #activity + date to database
                    if after.activity.name == "Spotify":
                        song_name = after.activity.title
                        user_logs = user_logs[0] + f",{after.activity.name} - {song_name}: {formatted_time}"
                    else:
                        user_logs = user_logs[0] + f",{after.activity.name}: {formatted_time}"
                    
                    cursor.execute("UPDATE user_activity_logs SET logs = ? WHERE user_id = ?", (user_logs, user_id))
                    connection.commit()
                    #log
                    print(f"{username} is now {after.activity.name}")
            else:
                #if user logs do not exist, create new row for the user
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                if after.activity.name == "Spotify":
                    song_name = after.activity.title
                    user_logs = f"{after.activity.name} - {song_name}: {formatted_time}"
                else:
                    user_logs = f"{after.activity.name}: {formatted_time}"
                cursor.execute("INSERT INTO user_activity_logs (user_id, username, logs) VALUES (?, ?, ?)", (user_id, username, user_logs))
                connection.commit()
                #log
                print(f"{username} is now {after.activity.name}")
   
            




@bot.tree.command(name="schedule")
async def schedule(interaction: discord.Interaction, user: discord.Member):
    #if channel is correct or user id is bot owner
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        try:
            file = plot_user(user.id)
            await interaction.followup.send(file=file)
            #log
            print(f"User {user.name} requested chart for {user.name} in {interaction.channel.name}")

        except:

            await interaction.followup.send("No data found", ephemeral=True)
     
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)

#command, get user's last online time
@bot.tree.command(name="lastonline")
async def lastonline(interaction: discord.Interaction, user: discord.Member):
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user.id,)).fetchone()
        if user_logs:
            user_logs = user_logs[0].split(",")
            last_online = user_logs[-1].split(": ")[1]
            await interaction.followup.send(f"{user.name} was last online at {last_online}", ephemeral=True)
        else:
            await interaction.followup.send(f"{user.name} has no logs", ephemeral=True)
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#command for dumping user_activity_logs for user
@bot.tree.command(name="activitylog")
async def activity(interaction: discord.Interaction, user: discord.Member, limit: int = 10):
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        user_logs = cursor.execute("SELECT logs FROM user_activity_logs WHERE user_id = ?", (user.id,)).fetchone()
        if user_logs:
            user_logs = get_last_n_records(user_logs[0], limit)
            try:
                await interaction.followup.send(f"{user_logs}")
            except:
                await interaction.followup.send(f"Exceeds 2000 characters")
        else:
            await interaction.followup.send(f"{user.name} has no activity logs")
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#command for dumping user_logs for user
@bot.tree.command(name="onlinelog")
async def activity(interaction: discord.Interaction, user: discord.Member, limit: int = 10):
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user.id,)).fetchone()
        if user_logs:
            user_logs = get_last_n_records(user_logs[0], limit)
            try:
                await interaction.followup.send(f"{user_logs}")
            except:
                await interaction.followup.send(f"Exceeds 2000 characters")
        else:
            await interaction.followup.send(f"{user.name} has no activity logs")
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#command that deletes row of user from user_logs
@bot.tree.command(name="deletelog")
async def deleteuser(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        cursor.execute("DELETE FROM user_logs WHERE user_id = ?", (user.id,))
        connection.commit()
        await interaction.followup.send(f"{user.name} deleted from user_logs")
    else:
        await interaction.response.send_message("You dont have permission", ephemeral=True)

#command that deletes row of user from user_activity_logs
@bot.tree.command(name="deleteactivitylog")
async def deleteuser(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id == 334013974704029700:
        await interaction.response.defer() 
        cursor.execute("DELETE FROM user_activity_logs WHERE user_id = ?", (user.id,))
        connection.commit()
        await interaction.followup.send(f"{user.name} deleted from user_activity_logs")
    else:
        await interaction.response.send_message("You dont have permission", ephemeral=True)



#bot run
bot.run(TOKEN)
