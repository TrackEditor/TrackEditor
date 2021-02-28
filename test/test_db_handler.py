import pytest
import pandas as pd

from db_handler import DbHandler
import constants as c
import iosm


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


def get_db() -> DbHandler:
    # Ease the creation of data base handler
    dbh = DbHandler()
    dbh.open_db()
    return dbh


@pytest.fixture(scope="session", autouse=True)
def remove_test_files():
    # Remove test tile from db if exists
    dbh = get_db()
    for zoom in range(c.max_zoom + 1):
        xtiles, ytiles = area_tiles(zoom)

        for x in xtiles:
            for y in ytiles:
                dbh.remove_tile(zoom, x, y)


def test_open_db():
    dbh = DbHandler()
    assert dbh.open_db()


def test_print_db():
    dbh = get_db()
    assert isinstance(dbh.print_tiles(verbose=False), type(pd.DataFrame()))


def test_insert_tile():
    dbh = get_db()
    xtiles, ytiles = area_tiles(c.max_zoom)
    dbh.insert_tile(c.max_zoom, xtiles.start, ytiles.start,
                    True, "/hello", 512)
    assert dbh._tile_exists(c.max_zoom, xtiles.start, ytiles.start)


def test_remove_tile():
    dbh = get_db()
    xtiles, ytiles = area_tiles(c.max_zoom)
    dbh.remove_tile(c.max_zoom, xtiles.start, ytiles.start)
    assert not dbh._tile_exists(c.max_zoom, xtiles.start, ytiles.start)


def test_close_db():
    dbh = get_db()
    try:  # no exception in dbh makes it good
        dbh.close_db()
        assert True
    except Exception:
        assert False


def test_get_tile_size():
    dbh = get_db()
    xtiles, ytiles = area_tiles(c.max_zoom)

    # Create test tile
    dbh.remove_tile(c.max_zoom, xtiles.start, ytiles.start)
    dbh.insert_tile(c.max_zoom, xtiles.start, ytiles.start,
                    True, "/bye", 2048)  # uses end tiles

    # Test
    assert dbh.get_tile_size(c.max_zoom, xtiles.start, ytiles.start) == 2048


def test_get_tile_status():
    dbh = get_db()
    xtiles, ytiles = area_tiles(c.max_zoom)

    # Create test tile
    dbh.remove_tile(c.max_zoom, xtiles.start, ytiles.start)
    dbh.insert_tile(c.max_zoom, xtiles.start, ytiles.start,
                    False, "/bye", 1028)
    # Test
    assert not dbh.get_tile_status(c.max_zoom, xtiles.start, ytiles.start)


def test_update_tile_status():
    dbh = get_db()
    xtiles, ytiles = area_tiles(c.max_zoom)

    # Create test tile
    dbh.remove_tile(c.max_zoom, xtiles.start, ytiles.start)
    dbh.insert_tile(c.max_zoom, xtiles.start, ytiles.start,
                    False, "/bye", 1028)  # uses end tiles

    # Test
    dbh.update_tile_status(c.max_zoom, xtiles.start, ytiles.start, True, 2042)
    assert dbh.get_tile_status(c.max_zoom, xtiles.start, ytiles.start)


def test_tile_exists():
    dbh = get_db()
    dbh.insert_tile(1, 1, 0, True, "/test", 1028)

    assert dbh._tile_exists(1, 1, 0)
    assert not dbh._tile_exists(1, 1, 4)
