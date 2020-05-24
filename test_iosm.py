import pytest
import os

import iosm
import constants as c


def area_coor():
    # Define the area for test: Inaccessible Island in south Atlantic Ocean
    lon_min = -12.707272
    lon_max = -12.640879
    lat_min = -37.322413
    lat_max = -37.279825

    return lon_min, lon_max, lat_min, lat_max


def area_tiles(zoom):
    # Define tiles for test: Inaccessible Island in south Atlantic Ocean
    (lon_min, lon_max, lat_min, lat_max) = area_coor()
    min_xtile, min_ytile = iosm.deg2num(lat_max, lon_min, zoom)
    max_xtile, max_ytile = iosm.deg2num(lat_min, lon_max, zoom)
    return range(min_xtile, max_xtile + 1, 1),\
        range(min_ytile, max_ytile + 1, 1)


@pytest.fixture(scope="session", autouse=True)
def remove_test_files():
    # Remove test tiles if exists

    for zoom in range(c.max_zoom + 1):
        xtiles, ytiles = area_tiles(zoom)

        for x in xtiles:
            for y in ytiles:
                tile_path = f'tiles/{zoom}/{x}/{y}.png'
                if os.path.isfile(tile_path):
                    os.remove(tile_path)


def test_deg2num():
    # This function was copied from OSM wiki, no expected fail
    assert True


def test_num2deg():
    # This function was copied from OSM wiki, no expected fail
    assert True


def test_download_url_nominal():
    xtiles, ytiles = area_tiles(c.max_zoom)
    assert iosm._download_url(c.max_zoom, xtiles.start, ytiles.start)


def test_download_url_existing_tile():
    # Try to download nominal tile
    xtiles, ytiles = area_tiles(c.max_zoom)
    assert iosm._download_url(c.max_zoom, xtiles.start, ytiles.start)


def test_download_url_wrong_tile():
    fake_input = 12345689  # no tile for this value in zoom/x/y
    assert not iosm._download_url(fake_input, fake_input, fake_input)


def test_download_tiles_nominal():
    # Total number of tiles can differ according to zoom level
    expected_tiles = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 2,
                      9: 2, 10: 2, 11: 4, 12: 4, 13: 6, 14: 16}
    total_tiles = sum(expected_tiles.values())

    (lon_min, lon_max, lat_min, lat_max) = area_coor()
    assert \
        iosm.download_tiles(lat_min, lon_min, lat_max, lon_max, max_zoom=14) \
        == total_tiles
