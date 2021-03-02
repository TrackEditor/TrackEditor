import logging
from typing import Tuple
import pandas as pd
import numpy as np
import matplotlib.image as mpimg
import geopy.distance

import constants as c
import iosm
import track


logger = logging.getLogger(__name__)


def point_reduction(df_segment: pd.DataFrame):
    positions = sorted(list(set([int(pos) for pos in
                                 np.linspace(0, len(df_segment) - 1,
                                             c.max_displayed_points)]
                                )
                            )
                       )
    return df_segment.iloc[positions]


def get_map_box(extreme_tiles: Tuple[int, int, int, int], zoom: int) -> \
        Tuple[int, int, int, int]:
    xtile, ytile, final_xtile, final_ytile = extreme_tiles

    ymax, xmax = iosm.num2deg(final_xtile + 1, ytile, zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile + 1, zoom)

    bbox = (xmin, xmax, ymin, ymax)
    return bbox


def generate_map(ob_track: track.Track) -> np.array:

    # Define map perspective
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    zoom = auto_zoom(lat_min, lon_min, lat_max, lon_max)

    extreme_tiles = get_extreme_tiles(ob_track, zoom)
    logger.debug(f'{extreme_tiles}, {zoom}')

    # Download missing tiles
    logger.debug('download tiles')
    iosm.download_tiles_by_num(extreme_tiles[0], extreme_tiles[1],
                               extreme_tiles[2], extreme_tiles[3],
                               max_zoom=zoom, extra_tiles=c.margin_outbounds)
    logger.debug('generate map')
    # Generate map image
    map_img = create_map_img(extreme_tiles, zoom)

    # Define map box
    bbox = get_map_box(extreme_tiles, zoom)

    return map_img, bbox


def get_click_distance(bbox):
    click_distance = 0.05 * abs(geopy.distance.geodesic(
        [bbox[0], bbox[2]],
        [bbox[1], bbox[3]]).km)
    return click_distance


def get_ntail_dimension(init_tile, end_tile):

    length = abs(end_tile - init_tile)

    # Create nxn tiles box
    if length < c.map_size:
        if length == 0:
            end_tile += 1
            if length > 0:
                init_tile -= 1
            else:
                end_tile += 1
        if length == 1:
            end_tile += 1
    elif length > c.map_size:
        logger.error('Size reduction!')
        i = 0
        while length > c.map_size:
            if i % 2 == 1:
                end_tile -= 1
            else:
                init_tile += 1
            length = abs(end_tile - init_tile)
    return init_tile, end_tile


def get_extreme_tiles(ob_track: track.Track, zoom: int):
    # Get extreme tiles to fit coordinates
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    xtile, ytile = iosm.deg2num(lat_max, lon_min, zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, zoom)

    logger.debug(f'{(xtile, ytile, final_xtile, final_ytile)}, {zoom}')

    # Regularize according to map size
    xtile, final_xtile = get_ntail_dimension(xtile, final_xtile)
    ytile, final_ytile = get_ntail_dimension(ytile, final_ytile)

    return xtile, ytile, final_xtile, final_ytile


def create_map_img(extreme_tiles: Tuple[int, int, int, int],
                   zoom: int) -> np.array:
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f'tiles/{zoom}/{x}/{ytile}.png')

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f'tiles/{zoom}/{x}/{y}.png'
            local_img = mpimg.imread(local_img_path)
            y_img = np.vstack((y_img, local_img))

        if map_img is not None:
            map_img = np.hstack((map_img, y_img))
        else:
            map_img = y_img

    return map_img


def auto_zoom(lat_min: float, lon_min: float,
              lat_max: float, lon_max: float) -> int:
    """
    Compute the best zoom to show a complete track. It must contain the full
    track in a box of nxn tails (n is specified in constants.py).
    :param lat_min: furthest south point
    :param lon_min: furthest west point
    :param lat_max: furthest north point
    :param lon_max: furthest east point
    :return: zoom to use to show full track
    """

    for zoom in range(c.max_zoom):
        num_x_min, num_y_min = iosm.deg2num(lat_min, lon_min, zoom)
        num_x_max, num_y_max = iosm.deg2num(lat_max, lon_max, zoom)

        width = abs(num_x_max - num_x_min)
        height = abs(num_y_max - num_y_min)

        logger.debug(
            f'auto_zoom: {zoom - 1}, width: {width}, height: {height}')
        if width > c.map_size or height > c.map_size:
            logger.debug(
                f'auto_zoom: {zoom -1}, width: {width}, height: {height}')
            return zoom - 1  # in this case previous zoom is the good one

        if (width == c.map_size and height < c.map_size) or \
                (width < c.map_size and height == c.map_size):
            # this provides bigger auto_zoom than using >= in previous case
            return zoom

    logger.debug(f'auto_zoom: {c.max_zoom} (this is c.max_zoom)')
    return c.max_zoom
