import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import sqlite3


#connect to database
connection = sqlite3.connect('log_data.db')
# parse the data from the database
data_str = connection.execute("SELECT logs FROM user_logs WHERE user_id = ?", ("334013974704029700",)).fetchone()[0]


data_str = "online: 2023-03-01 09:15:00,offline: 2023-03-01 23:30:00,online: 2023-03-02 08:50:00,offline: 2023-03-02 23:15:00,online: 2023-03-03 09:05:00,offline: 2023-03-03 22:45:00,online: 2023-03-04 09:20:00,offline: 2023-03-04 23:00:00,online: 2023-03-05 10:30:00,offline: 2023-03-05 14:30:00,online: 2023-03-05 19:00:00,offline: 2023-03-05 23:00:00,online: 2023-03-06 09:10:00,offline: 2023-03-06 23:10:00,online: 2023-03-07 09:30:00,offline: 2023-03-07 23:20:00,online: 2023-03-08 08:55:00,offline: 2023-03-08 23:05:00,online: 2023-03-09 09:25:00,offline: 2023-03-09 23:15:00,online: 2023-03-10 09:15:00,offline: 2023-03-10 23:00:00,online: 2023-03-11 09:05:00,offline: 2023-03-11 22:50:00,online: 2023-03-12 09:20:00,offline: 2023-03-12 22:55:00,online: 2023-03-13 09:10:00,offline: 2023-03-13 22:45:00,online: 2023-03-14 09:00:00,offline: 2023-03-14 23:00:00"

data_list = data_str.split(",")
datetime_list = []
for d in data_list:
    if d.startswith("online"):
        datetime_list.append(dt.datetime.strptime(d.split(": ")[1], "%Y-%m-%d %H:%M:%S"))
    elif d.startswith("offline"):
        datetime_list.append(dt.datetime.strptime(d.split(": ")[1], "%Y-%m-%d %H:%M:%S"))


# create the 2D array
day_start = datetime_list[0].date()
day_end = datetime_list[-1].date() + dt.timedelta(days=1)
hours = np.arange(24)
days = np.arange((day_end - day_start).days)
arr = np.zeros((24, len(days)), dtype=int)
for i in range(0, len(datetime_list)-1, 2):  # added -1 to the range and updated the step to 2
    start, end = datetime_list[i], datetime_list[i+1]
    day = (start.date() - day_start).days
    start_hour = start.hour
    end_hour = end.hour if end.date() == start.date() else 24
    arr[start_hour:end_hour, day] = 1


# plot the array
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_aspect("auto")
cmap =  ListedColormap(["red", "blue"])
im = ax.pcolormesh(days, hours, arr, cmap=cmap, vmin=0, vmax=1)
ax.set_xticks(days+0.5)
ax.set_xticklabels([(day_start+dt.timedelta(days=int(i))).strftime("%Y-%m-%d") for i in days])
ax.set_yticks(hours+0.5)
ax.set_yticklabels([f"{h:02d}:00" for h in hours])
ax.set_xlabel("Day")
ax.set_ylabel("Hour")
#fig.colorbar(im, ax=ax)
plt.show()

fig.savefig("static/images/renkochart.png")