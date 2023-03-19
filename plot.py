from functions import *
import sqlite3
import discord
import pytz
import datetime
from database import get_database_connection, get_database_cursor

connection = get_database_connection()
cursor = get_database_cursor(connection)

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

#function that creates plot from data
def plot_data(data_pairs, id, username):

    df = pd.DataFrame(data_pairs, columns=["start_str", "end_str"])

    df["start_time"] = pd.to_datetime(df["start_str"].apply(lambda x: x.split(": ")[1]))
    df["end_time"] = pd.to_datetime(df["end_str"].apply(lambda x: x.split(": ")[1]))

    df.drop(["start_str", "end_str"], axis=1, inplace=True)

    df["start_datetime"] = pd.to_datetime(df["start_time"])
    df["end_datetime"] = pd.to_datetime(df["end_time"])
    df["start_time"] = df["start_datetime"].dt.time
    df["end_time"] = df["end_datetime"].dt.time
    df["start_date"] = df["start_datetime"].dt.date

    df_no_cross = df[df["start_datetime"].dt.day == df["end_datetime"].dt.day].copy()
    df_cross = df[df["start_datetime"].dt.day != df["end_datetime"].dt.day]
    df_cross_1 = df_cross.copy()
    df_cross_2 = df_cross.copy()
    df_cross_1["end_time"] = datetime.time(hour=23, minute=59, second=59)
    df_cross_2["start_date"] = df_cross_2["start_date"] + datetime.timedelta(days=1)
    df_cross_2["start_time"] = datetime.time(hour=0, minute=0, second=0)

    rows_no_cross = df_no_cross[["start_date", "start_time", "end_time"]]
    rows_cross_1 = df_cross_1[["start_date", "start_time", "end_time"]]
    rows_cross_2 = df_cross_2[["start_date", "start_time", "end_time"]]
    rows = pd.concat([rows_no_cross, rows_cross_1, rows_cross_2])

    rows["start_time"] = pd.to_datetime(rows["start_time"], format='%H:%M:%S')
    rows["end_time"] = pd.to_datetime(rows["end_time"], format='%H:%M:%S')

    date_range = pd.date_range(start=rows["start_date"].min(), end=rows["start_date"].max(), freq="1D")

    num_days = len(date_range)
    #print(f"Number of days:  {num_days}")

    

    if num_days >= 90:
        date_breaks = "1 month"
        date_labels = "%b %Y"
    elif num_days >= 30:
        date_breaks = "1 week"
        date_labels = "%m-%d"
    elif num_days >= 7:
        date_breaks = "3 day"
        date_labels = "%m-%d"
    elif num_days >= 2:
        date_breaks = "1 day"
        date_labels = "%m-%d"
    else:
        date_breaks = "1 day"
        date_labels = "%m-%d"

    column_width = 250 / num_days

    text_color = "#FFFFFF"
    background_color = "#262626"
    element_color = "#B653F2"
    element_color = shift_hue(element_color, random.random())

    plot = (ggplot(aes(x="start_date"), rows)
    + geom_segment(aes(xend="start_date", yend="end_time", y="start_time"), size=column_width, color=element_color)
    + scale_x_date(name="", date_breaks=date_breaks, date_labels=date_labels, expand=(0, 0)) 
    + scale_y_datetime(date_labels="%H:%M", expand=(0, 0, 0, 0.0001), date_breaks="1 hour")
    + ggtitle(f"{username}'s activity graph")
    + theme(plot_background=element_rect(fill=background_color, color=background_color), panel_background=element_rect(fill=background_color), axis_title=element_blank(), text=element_text(color=text_color), panel_grid_major = element_blank(), panel_grid_minor = element_blank())
    )
    username = re.sub('[^0-9a-zA-Z]+', '', username)

    ggsave(plot, f"static/plots/{username}_{id}.png", width=6.96, height=5.51, units="in", dpi=300)
    file = discord.File(f"static/plots/{username}_{id}.png")
    #print(file)
    return file


#plot_user(778732258080063510)