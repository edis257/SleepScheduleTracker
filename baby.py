from functions import *
import sqlite3
import discord
import pytz
import datetime

connection = sqlite3.connect('log_data.db')

#function where you input user id and it returns a plot
def plot_user(user_id):
    data_str = connection.execute("SELECT logs FROM user_logs WHERE user_id = ?", (user_id,)).fetchone()[0]
    #select from database username where id = user_id
    username = connection.execute("SELECT username FROM user_logs WHERE user_id = ?", (user_id,)).fetchone()[0]

    try:
        data_str = convert(data_str)
        data_list = data_str.split(",")
        data_pairs = data_pair_creator(data_list)
        #print(data_pairs)
        file = plot_data(data_pairs, user_id, username)

    except:
        tz = pytz.timezone('Europe/Vilnius')
        current_time = datetime.datetime.now(tz)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        data_str += f",offline: {formatted_time}"

        
        data_str = convert(data_str)


        data_list = data_str.split(",")
        data_pairs = data_pair_creator(data_list)
        file = plot_data(data_pairs, user_id, username)

    return file


#plot_user(1017486239370313860)

def plot_all_users():
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, username FROM user_logs")
    users = cursor.fetchall()

    for user in users:
        # print user id
        print("#" * 50)
        print(user[1])
        print("#" * 50)
        plot_user(user[0])

    connection.close()

#plot_all_users()


