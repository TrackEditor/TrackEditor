import gpx
import logging
import datetime as dt
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import numpy as np

import constants as c
import iosm


def auto_zoom(lat_min: float, lon_min: float,
              lat_max: float, lon_max: float) -> int:
    """
    Compute the best zoom to show a complete track. It must contain the full
    track in more than one tail but minimising the number of tails.
    :param lat_min: furthest south point
    :param lon_min: furthest west point
    :param lat_max: furthest north point
    :param lon_max: furthest east point
    :return: zoom to use to show full track
    """

    for zoom in range(c.max_zoom):
        num_x_min, num_y_min = iosm.deg2num(lat_min, lon_min, zoom)
        num_x_max, num_y_max = iosm.deg2num(lat_max, lon_max, zoom)

        number_tiles = abs((num_x_max - num_x_min) * (num_y_max - num_y_min))

        if number_tiles > 1:
            return zoom

    return c.max_zoom


if __name__ == "__main__":
    # Define logger
    if not os.path.isdir("log"):
        os.mkdir("log")

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime("%Y%m%d-%H%M%S")

    logging.basicConfig(level=c.log_level,
                        filename=f"log/{date_time}_track_editor.log")
    logger = logging.getLogger()

    # Load gpx file
    my_route = "test_cases/nominal_route.gpx"
    gpx_track = gpx.Gpx(my_route)
    pd_track = gpx_track.to_pandas()

    # Get extremes values
    lat_min = pd_track["lat"].min()
    lat_max = pd_track["lat"].max()
    lon_min = pd_track["lon"].min()
    lon_max = pd_track["lon"].max()

    # Select optimal zoom
    zoom = auto_zoom(lat_min, lon_min, lat_max, lon_max)

    # Download OSM tiles if needed
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max)

    # Get map image
    xtile, ytile = iosm.deg2num(lat_max, lon_min, zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, zoom)

    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f"tiles/{zoom}/{x}/{ytile}.png")

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f"tiles/{zoom}/{x}/{y}.png"
            local_img = mpimg.imread(local_img_path)
            y_img = np.vstack((y_img, local_img))

        if map_img is not None:
            map_img = np.hstack((map_img, y_img))
        else:
            map_img = y_img

    # Plots
    plt.figure()
    gspec = gridspec.GridSpec(4, 1)

    # Plot map
    plt.subplot(gspec[:3, 0])
    ax = plt.gca()
    ymax, xmax = iosm.num2deg(final_xtile+1, ytile, zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile+1, zoom)
    BBox = (xmin, xmax, ymin, ymax)
    ax.imshow(map_img, zorder=0, extent=BBox, aspect='equal')

    # Plot track
    ax.scatter(pd_track.lon, pd_track.lat, s=5)

    # Beauty salon
    plt.tick_params(axis="x", bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis="y", left=False, right=False, labelleft=False)

    ax.set_xlim((xmin, xmax))
    ax.set_ylim((ymin, ymax))

    # Plot elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        ax = plt.gca()
        ax.fill_between(np.arange(len(pd_track)), pd_track.ele)
        ax.set_ylim((pd_track.ele.min()*0.8, pd_track.ele.max()*1.2))

    # TODO: tkinter https://www.youtube.com/watch?v=jBUpjijYtCk
    # TODO: tutoriales tkinter: https://www.youtube.com/playlist?list=PLQVvvaa0QuDclKx-QpC9wntnURXVJqLyk


    plt.show()
