import discord
from discord.ext import commands
from datetime import datetime
from discord.ext import commands
import pytz
import os
import tempfile
from discord import app_commands

#how to install discord components?
#pip install discord-components

from plot import plot_user
from functions import get_last_n_records, convert
from leaderboard import show_leaderboard

from database import get_database_connection, get_database_cursor



connection = get_database_connection()
cursor = get_database_cursor(connection)

TOKEN = os.getenv('DISCORD_TOKEN')
interaction_channel = int(os.getenv('INTERACTION_CHANNEL'))
interaction_id = int(os.getenv('INTERACTION_ID'))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

tz = pytz.timezone('Europe/Vilnius')

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
    user_id = str(after.id)
    is_ignored = cursor.execute("SELECT 1 FROM ignored_users WHERE user_id = ?", (user_id,)).fetchone()
    if is_ignored:
        return
    # Rest of the code
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
                    user_logs = user_logs[0] + f",{formatted_time}: {after.activity.name} - {song_name}"
                else:
                    user_logs = user_logs[0] + f",{formatted_time}: {after.activity.name}"
                    
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
                    user_logs = f"{formatted_time}: {after.activity.name} - {song_name}"
                else:
                    user_logs = f"{formatted_time}: {after.activity.name}"
                cursor.execute("INSERT INTO user_activity_logs (user_id, username, logs) VALUES (?, ?, ?)", (user_id, username, user_logs))
                connection.commit()
                #log
                print(f"{username} is now {after.activity.name}")


#1
@bot.tree.command(name="graph", description="Get the activity graph for a user")
@app_commands.describe(user="User to get graph for")
async def schedule(interaction: discord.Interaction, user: discord.Member):
    #if channel is correct or user id is bot owner
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == interaction_id:
        await interaction.response.defer() 
        try:
            file = plot_user(user.id)
            await interaction.followup.send(file=file)
            #log
            print(f"User {interaction.user} requested chart for {user.name} in {interaction.channel.name}")

        except:

            await interaction.followup.send("No data found", ephemeral=True)
     
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#2
@bot.tree.command(name="activitylog", description="Get the activity log for a user")
@app_commands.describe(user="User to get logs for", limit="Number of logs to get (default 100)")
async def activity(interaction: discord.Interaction, user: discord.Member, limit: int = 100):
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == interaction_id:
        await interaction.response.defer() 
        user_logs = cursor.execute("SELECT logs FROM user_activity_logs WHERE user_id = ?", (user.id,)).fetchone()
        if user_logs:
            user_logs = get_last_n_records(user_logs[0], limit)
            # Create a temporary file and write the records
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
                temp_file.write(user_logs)
                temp_path = temp_file.name

            # Send the file as an attachment
            try:
                with open(temp_path, 'rb') as attachment_file:
                    attachment = discord.File(attachment_file, f"{user.name}_activity_logs.txt")
                    await interaction.followup.send(file=attachment)
            except:
                await interaction.followup.send(f"Error sending file")
            finally:
                # Remove the temporary file
                os.remove(temp_path)
        else:
            await interaction.followup.send(f"{user.name} has no activity logs")
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)



#3
@bot.tree.command(name="onlinelog", description="Get online logs for a user")
@app_commands.describe(user="User to get logs for", limit="Number of logs to get (default 100)")
async def onlinelog(interaction: discord.Interaction, user: discord.Member, limit: int = 100):
    if interaction.channel_id == int(interaction_channel) or interaction.user.id == interaction_id:
        await interaction.response.defer() 
        user_logs = cursor.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user.id,)).fetchone()
        print(user_logs)
        #print t
        #user_logs = convert(user_logs[0])
        #print(user_logs)
        if user_logs:
            user_logs = get_last_n_records(user_logs[0], limit)
            # Create a temporary file and write the records
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
                temp_file.write(user_logs)
                temp_path = temp_file.name

            # Send the file as an attachment
            try:
                with open(temp_path, 'rb') as attachment_file:
                    attachment = discord.File(attachment_file, f"{user.name}_online_logs.txt")
                    await interaction.followup.send(file=attachment)
            except:
                await interaction.followup.send(f"Error sending file")
            finally:
                # Remove the temporary file
                os.remove(temp_path)
        else:
            await interaction.followup.send(f"{user.name} has no activity logs")
    else:
        await interaction.response.send_message("Bad channel", ephemeral=True)


#4
@bot.tree.command(name="deletelog")
async def deleteuserlog(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id == interaction_id:
        await interaction.response.defer() 
        cursor.execute("DELETE FROM user_logs WHERE user_id = ?", (user.id,))
        connection.commit()
        await interaction.followup.send(f"{user.name} deleted from user_logs")
    else:
        await interaction.response.send_message("You dont have permission", ephemeral=True)

#5
@bot.tree.command(name="deleteactivitylog")
async def deleteuseractivitylog(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id == interaction_id:
        await interaction.response.defer() 
        cursor.execute("DELETE FROM user_activity_logs WHERE user_id = ?", (user.id,))
        connection.commit()
        await interaction.followup.send(f"{user.name} deleted from user_activity_logs")
    else:
        await interaction.response.send_message("You dont have permission", ephemeral=True)

#6
@bot.tree.command(name="ignoreuser")
async def ignoreuser(interaction: discord.Interaction, user: discord.Member, action: str):
    if interaction.user.id == interaction_id:
        if action.lower() == "add":
            cursor.execute("INSERT OR IGNORE INTO ignored_users (user_id) VALUES (?)", (str(user.id),))
            connection.commit()
            await interaction.response.send_message(f"{user.name} has been added to the ignore list.", ephemeral=True)
        elif action.lower() == "remove":
            cursor.execute("DELETE FROM ignored_users WHERE user_id = ?", (str(user.id),))
            connection.commit()
            await interaction.response.send_message(f"{user.name} has been removed from the ignore list.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid action", ephemeral=True)
    else:
        await interaction.response.send_message("You dont have permission", ephemeral=True)


#7
@bot.tree.command(name="leaderboard", description="Show online total leaderboard of current month")
@app_commands.describe(limit="The number of users to show")
async def showleaderboard(interaction: discord.Interaction, limit: int = 10):
    leaderboard = show_leaderboard(limit)

    embed = discord.Embed(title="Leaderboard", description="Top users by online time", color=0x42F56C)

    leaderboard_content = ""
    for index, username, online_time in leaderboard:
        line = f"{index}. {username.ljust(20)} {online_time}\n"
        # Check if adding the line would exceed the character limit
        if len(leaderboard_content) + len(line) > 6000:  # The max limit for embeds is 6000 characters, not 2000
            break
        leaderboard_content += line

    embed.description = f"```{leaderboard_content}```"

    await interaction.response.send_message(embed=embed)

#bot run
bot.run(TOKEN)
