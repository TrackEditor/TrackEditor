"""
i: interface
osm: open street map
"""
import os
import math
import logging
from urllib3 import PoolManager

import constants as c
from db_handler import DbHandler

LOGGER = logging.getLogger(__name__)

DBH = DbHandler()


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> (int, int):
    """
    Get OSM tiles from coordinates and zoom.
    :param lat_deg: latitude in degrees
    :param lon_deg: longitude in degrees
    :param zoom: zoom grade
    :return: x-y tile
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def num2deg(xtile: int, ytile: int, zoom: int) -> (float, float):
    """
    Get OSM coordinates from tile index and zoom.
    :param xtile: x index
    :param ytile: y index
    :param zoom: zoom grade
    :return: latitude, longitude of NW corner
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def _download_url(zoom: int, xtile: int, ytile: int) -> bool:
    """
    Manage URL request to download tiles from OSM
    :param zoom: zoom grade
    :param xtile: OSM X-tile
    :param ytile: OSM Y-tile
    :return: True if tile is correct
    """
    # Define path
    dir_path = f'{c.prj_path}/tiles/{zoom}/{xtile}/'
    tile_path = f'{dir_path}/{ytile}.png'
    if not os.path.exists(dir_path):
        LOGGER.debug(f'Creating directory: {dir_path}')
        os.makedirs(dir_path)

    # Check if request is needed
    if os.path.isfile(tile_path):
        if DBH.get_tile_size(zoom, xtile, ytile) > 0:
            LOGGER.info(f'Tile ({zoom},{xtile},{ytile}) ' +
                        f'is already available at {tile_path}')
            return True
        else:
            DBH.remove_tile(zoom, xtile, ytile)
    else:
        DBH.remove_tile(zoom, xtile, ytile)

    # Request
    user_agent = {'user-agent': f'{c.tool} {c.version} {c.email}'}
    http = PoolManager(headers=user_agent)
    url = f'https://a.tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png'
    LOGGER.debug(f'Request to: {url}')

    response = http.request('GET', url)

    # Store content
    with open(tile_path, 'wb') as destination:
        if response.status == 200:
            destination.write(response.data)
            LOGGER.info(f'Tile ({zoom},{xtile},{ytile})' +
                        f'has been downloaded at {url}')
        else:
            # empty file has been created
            LOGGER.error(f'Error in request url={url},' +
                         f'reason={response.reason},' +
                         f'status={response.status}')
        destination.close()

    # Check downloaded info
    valid_tail = False
    request_size = response.headers.get("Content-Length")
    tile_size = os.stat(tile_path).st_size

    if int(request_size) == tile_size:
        valid_tail = True
    else:
        LOGGER.error(f'Size check has failed for tail ' +
                     f'({zoom},{xtile},{ytile}) at {tile_path}')

    DBH.insert_tile(zoom, xtile, ytile, valid_tail, tile_path, tile_size)
    response.close()

    return valid_tail


def download_tiles_by_deg(lat_min: float, lon_min: float,
                          lat_max: float, lon_max: float,
                          max_zoom: int = c.max_zoom,
                          extra_tiles: int = 0) -> int:
    """
    Download all tiles in a selected square
    :param lat_min: furthest south point
    :param lon_min: furthest west point
    :param lat_max: furthest north point
    :param lon_max: furthest east point
    :param max_zoom: maximum level of zoom to download
    :param extra_tiles: surrounding tiles to download
    :return: total number of tiles in the area
    """
    DBH.open_db()  # open database for tiles
    total_tiles = 0  # initialize output counter

    for zoom in range(max_zoom + 1):
        xtile, ytile = deg2num(lat_max, lon_min, zoom)
        final_xtile, final_ytile = deg2num(lat_min, lon_max, zoom)

        for x in range(xtile - extra_tiles, final_xtile + 1 + extra_tiles, 1):
            for y in range(ytile - extra_tiles, final_ytile + 1 + extra_tiles,
                           1):
                if x >= 0 and y >= 0:
                    if _download_url(zoom, x, y):
                        total_tiles += 1
    DBH.close_db()

    return total_tiles


def download_tiles_by_num(xtile: int, ytile: int,
                          final_xtile: int, final_ytile: int,
                          max_zoom: int = c.max_zoom,
                          extra_tiles: int = 0) -> int:
    """
    Download all tiles in a selected square
    :param xtile: left most tile
    :param ytile: top most tile
    :param final_xtile: right most tile
    :param final_ytile: bottom most tile
    :param max_zoom: maximum level of zoom to download
    :param extra_tiles: surrounding tiles to download
    :return: total number of tiles in the area
    """
    DBH.open_db()  # open database for tiles
    total_tiles = 0  # initialize output counter

    for x in range(xtile - extra_tiles, final_xtile + 1 + extra_tiles, 1):
        for y in range(ytile - extra_tiles, final_ytile + 1 + extra_tiles,
                       1):
            if x >= 0 and y >= 0:
                if _download_url(max_zoom, x, y):
                    total_tiles += 1
    DBH.close_db()

    return total_tiles
