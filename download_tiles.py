import os
import math
import time
import logging
from urllib3 import PoolManager

import constants as c

LOGGER = logging.getLogger(__name__)


# def deg2num(lat_deg, lon_deg, zoom):
#     """
#     Get OSM tiles from coordinates and zoom.
#     :param lat_deg: latitude in degrees
#     :param lon_deg: longitude in degrees
#     :param zoom: zoom grade
#     :return: x-y tile
#     """
#     lat_rad = math.radians(float(lat_deg))
#     n = 2.0 ** zoom
#     x_tile = int((float(lon_deg) + 180.0) / 360.0 * n)
#     y_tile = int((1.0 - math.log(float(math.tan(lat_rad) + 1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
#     return x_tile, y_tile


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def download_url(zoom, x_tile, y_tile):
    """
    Manage URL request to download tiles
    :param zoom: zoom grade
    :param x_tile: OSM X-tile
    :param y_tile: OSM Y-tile
    :return: None
    """
    # Define path
    dir_path = f"tiles/{zoom}/{x_tile}/"
    download_path = f"{dir_path}/{y_tile}.png"
    if not os.path.exists(dir_path):
        LOGGER.debug(f"Creating directory: {dir_path}")
        os.makedirs(dir_path)

    # Request
    user_agent = {'user-agent': 'TrackEditor V1 alguerre@outlook.com'}
    http = PoolManager(headers=user_agent)
    url = f"https://a.tile.openstreetmap.org/{zoom}/{x_tile}/{y_tile}.png"
    LOGGER.debug(f"Request to: {url}")

    response = http.request('GET', url)
    response.close()

    # Store content
    with open(download_path, 'wb') as destination:
        destination.write(response.data)
        destination.close()


def download_tiles(lat_min, lon_min, lat_max, lon_max):
    for zoom in range(c.max_zoom):

        x_tile, y_tile = deg2num(lat_max, lon_min, zoom)
        final_xtile, final_ytile = deg2num(lat_min, lon_max, zoom)

        for x in range(x_tile, final_xtile + 1, 1):
            for y in range(y_tile, final_ytile + 1, 1):
                download_url(zoom, x, y)
