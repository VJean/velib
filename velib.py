"""
Generate all sorts of static and animated charts based
on the available data.
"""

import json
import glob
import re
import tempfile
from bisect import bisect_left
from datetime import datetime, timezone
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from os.path import join as path_join
from PIL import Image
from matplotlib.gridspec import GridSpec

# box around Paris
paris_extent = [2.14, 2.55, 48.75, 48.96]  # TODO zoom juste a little bit more
# tiles server
tiles = cimgt.GoogleTiles()  # use projection and transform accordingly
data_crs = ccrs.PlateCarree()  # data are in lat/lon coordinates


def load_data():
    all_files = ['/home/jean/git/velib/records/201909%02d-velib-records.csv' % i for i in range(5, 24)]

    csvheaders = ["timestamp", "station_name", "lon", "lat", "mechanical", "ebike", "capacity", "numdocksavailable"]

    df = pd.concat((pd.read_csv(f, parse_dates=[0], index_col=[0], names=csvheaders) for f in all_files))

    # add columns with total of bikes in station and ratio of bikes available
    df['total_bikes'] = df['mechanical'] + df['ebike']
    df['occupation_ratio'] = df['total_bikes'] / df['capacity']

    # allow selection of a specific slice of time
    df = df["2019-09-16T15:00":"2019-09-16T17:00"]
    # allow selection of a specific slice of coordinates
    # df filter by lat / lon box

    return df


def bikes_distribution_over_time(df):
    # distribution over time of the number of bikes available by station
    groups = df.groupby(by=df.index)

    fig = plt.figure(figsize=(8, 6), dpi=100)
    fig.suptitle("Distribution of available bikes per station over time")
    locator = mdates.AutoDateLocator()
    fig.gca().xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    fig.gca().xaxis.set_major_locator(locator)
    fig.gca().set_xlabel("time")
    fig.gca().set_ylabel("bikes")

    agg = groups['total_bikes'].agg(['min',
                                     'median',
                                     lambda x: np.percentile(x, q=75),
                                     lambda x: np.percentile(x, q=90),
                                     lambda x: np.percentile(x, q=99),
                                     'max'])
    l_min, l_med, l_p75, l_p90, l_p99, l_max = plt.plot(agg)
    lines = [l_min, l_med, l_p75, l_p90, l_p99, l_max]
    labels = ["min", "med", "p75", "p90", "p99", "max"]

    fig.legend(lines[::-1], labels[::-1], loc="upper right")
    fig.savefig("bikes_per_station_over_time.png")


def number_of_docks(df):

    fig = plt.figure(figsize=(6, 6), dpi=100)
    fig.suptitle("Number of docks per station and spatial repartition")

    gs = GridSpec(2, 1, height_ratios=[1, 2])

    hist_axes = fig.add_subplot(gs[0])
    hist_axes.set_xlabel("number of docks")
    hist_axes.set_ylabel("stations")
    map_axes = fig.add_subplot(gs[1], projection=tiles.crs)
    map_axes.set_extent(paris_extent, crs=data_crs)

    series = df.groupby(by=['lon', 'lat'])[['capacity']].max()
    # some stations report a capacity of 0, but also available bikes... remove them
    series = series[series['capacity'] > 0]

    hist_axes.hist(series.values, bins=range(0, series['capacity'].max() + 5, 5))
    # TODO surround with histogram lat/lon (see gridspec examples)
    # https://matplotlib.org/3.2.1/gallery/lines_bars_and_markers/scatter_hist.html#sphx-glr-gallery-lines-bars-and-markers-scatter-hist-py
    map_axes.scatter(series.index.get_level_values(0), series.index.get_level_values(1), s=1, c=series['capacity'],
                                          cmap=plt.get_cmap('Reds'), transform=data_crs)  # TODO normalize data for cmap between 0,1 ?

    fig.savefig("total_docks.png")


def top_busy_stations(df):
    # Top 10 des stations les plus utilisées (avec le plus de changecount dans le nombre de vélos dispos)
    groups_stations = df[['station_name','total_bikes']].groupby(by=df['station_name'])

    return


def carto(df):

    station_count = df['station_name'].unique().size
    max_total_bikes = df['total_bikes'].max()

    groups = df.groupby(by=df.index)
    # TODO gridspec layout
    gs = GridSpec(2, 2, height_ratios=[3, 1])

    fig = plt.figure(figsize=(6, 7), dpi=100, clear=True)
    map_axes = fig.add_subplot(gs[0, :], projection=tiles.crs)
    map_axes.set_extent(paris_extent, crs=data_crs)
    # ax.add_image(tiles, 11)
    occupation_histo_axes = fig.add_subplot(gs[1, 0])
    occupation_histo_axes.set_title("Occupation")
    occupation_histo_axes.set_xlabel("occupation %")
    occupation_histo_axes.set_ylabel("stations")
    occupation_histo_axes.set_xlim(xmin=0, xmax=1)
    occupation_histo_axes.set_ylim(ymin=0, ymax=station_count)
    bike_count_histo_axes = fig.add_subplot(gs[1, 1], sharey=occupation_histo_axes)
    plt.setp(bike_count_histo_axes.get_yticklabels(), visible=False)
    bike_count_histo_axes.set_title("Total bikes in station")
    bike_count_histo_axes.set_xlabel("bikes")
    bike_count_histo_axes.set_xlim(xmin=0, xmax=max_total_bikes)

    frames = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        for ts, events in groups:
            # plot data
            map_points = map_axes.scatter(events['lon'], events['lat'], s=1, c=events['occupation_ratio'],
                                          cmap=plt.get_cmap('viridis_r'), transform=data_crs)
            occupation_histo_axes.hist(events['occupation_ratio'], bins=10, range=[0, 1])
            bike_count_histo_axes.hist(events['total_bikes'], range=[0, max_total_bikes])
            # set current date as the title of the figure
            plt.suptitle(ts.strftime('%Y-%m-%d %H:%M%z'))
            # save figure
            figfilename = ts.strftime('%Y%m%d%H%M%S.png')
            figfilepath = path_join(tmpdirname, figfilename)
            plt.savefig(figfilepath)
            # load figure as GIF frame
            new_frame = Image.open(figfilepath)
            frames.append(new_frame.copy())
            # clear subplots before next plot
            map_points.remove()  # just remove points and not map background
            occupation_histo_axes.cla()
            occupation_histo_axes.set_xlim(xmin=0, xmax=1)
            occupation_histo_axes.set_ylim(ymin=0, ymax=station_count)
            occupation_histo_axes.set_title("Occupation")
            occupation_histo_axes.set_xlabel("occupation %")
            occupation_histo_axes.set_ylabel("stations")
            bike_count_histo_axes.cla()
            bike_count_histo_axes.set_title("Total bikes in station")
            bike_count_histo_axes.set_xlabel("bikes")
            bike_count_histo_axes.set_xlim(xmin=0, xmax=max_total_bikes)
            plt.setp(bike_count_histo_axes.get_yticklabels(), visible=False)

        plt.close()
        frames[0].save('velib.gif', save_all=True, append_images=frames[1:], duration=(1000 / 60), loop=0)


if __name__ == "__main__":
    df = load_data()
    # top_busy_stations(df)
    # bikes_distribution_over_time(df)
    # number_of_docks(df)
    carto(df)

