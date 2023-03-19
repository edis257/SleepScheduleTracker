import datetime
import discord
import pandas as pd
from plotnine import *
import random

import re

from colorsys import rgb_to_hls, hls_to_rgb


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

#function that takes color and shift and returns color
def shift_hue(color, shift):
    r, g, b = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    h, l, s = rgb_to_hls(r/255, g/255, b/255)
    h = (h + shift) % 1
    r, g, b = tuple(round(c*255) for c in hls_to_rgb(h, l, s))
    hexcode = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)
    return hexcode


def get_last_n_records(records_string, n):
    records = records_string.split(',')
    if n >= len(records):
        return '\n'.join(records)
    else:
        return '\n'.join(records[-n:])

