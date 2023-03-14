import datetime
import discord
import pandas as pd
from plotnine import *

import re


#function that takes string and returns string
def convert(data_str):
    # Split the data string into a list of tuples
    data_list = [(x.strip().split(': ')[0], x.strip().split(': ')[1]) for x in data_str.split(',')]

    # Iterate through the list and remove consecutive tuples with the same status
    i = 1
    while i < len(data_list):
        if data_list[i][0] == data_list[i-1][0]:
            data_list.pop(i)
        else:
            i += 1

    # Convert the list of tuples back into a string
    data_str = ','.join([f"{x[0]}: {x[1]}" for x in data_list])
    
    return data_str


def data_pair_creator(data_list):
    data_pairs = []
    for i in range(0, len(data_list), 2):
        if i + 1 < len(data_list) and "online" in data_list[i] and "offline" in data_list[i + 1]:
            data_pairs.append((data_list[i], data_list[i + 1]))
    return data_pairs

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

    plot = (ggplot(aes(x="start_date"), rows)
    + geom_segment(aes(xend="start_date", yend="end_time", y="start_time"), size=column_width, color="green")
    + scale_x_date(name="", date_breaks=date_breaks, date_labels=date_labels, expand=(0, 0)) 
    + scale_y_datetime(date_labels="%H:%M", expand=(0, 0, 0, 0.0001), date_breaks="1 hour")
    + ggtitle(f"{username}'s activity schedule")
    + theme(plot_background=element_rect(color="white"), axis_title=element_blank())
    )

    username = re.sub('[^0-9a-zA-Z]+', '', username)


    ggsave(plot, f"static/images/{username}_{id}.png", width=6.96, height=5.51, units="in", dpi=300)
    file = discord.File(f"static/images/{username}_{id}.png")
    print(file)
    return file

