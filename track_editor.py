import gpx
import logging
import datetime as dt
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

import constants as c
import iosm


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

    # Download OSM tiles if needed
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max)

    # Get map image
    xtile, ytile = iosm.deg2num(lat_max, lon_min, c.max_zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, c.max_zoom)

    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f"tiles/{c.max_zoom}/{x}/{ytile}.png")

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f"tiles/{c.max_zoom}/{x}/{y}.png"
            local_img = mpimg.imread(local_img_path)
            y_img = np.vstack((y_img, local_img))

        if map_img is not None:
            map_img = np.hstack((map_img, y_img))
        else:
            map_img = y_img

    # Plot track
    plt.figure()
    plt.scatter(pd_track.lon, pd_track.lat, s=5)
    plt.xlabel("longitude")
    plt.ylabel("latitude")
    plt.axis("equal")

    # Plot map
    ymax, xmax = iosm.num2deg(final_xtile+1, ytile, c.max_zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile+1, c.max_zoom)
    BBox = (xmin, xmax, ymin, ymax)
    plt.imshow(map_img, zorder=0, extent=BBox, aspect='equal')

    plt.scatter(xmin, ymax, s=10, color="r")
    plt.scatter(xmax, ymin, s=10, color="r")

    plt.show()
