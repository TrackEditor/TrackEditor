import pytest
import datetime as dt
import os

from src import gpx

TEST_PATH = os.path.dirname(__file__)


def fail():
    return False


def test_load_file():
    route = gpx.Gpx(f"{TEST_PATH}/test_cases/basic_sample.gpx")
    assert route._load_file()


def test_load_file_big():
    route = gpx.Gpx(f"{TEST_PATH}/test_cases/over_10mb.gpx")
    assert route._load_file() is None


def test_load_file_no_permission():
    route = gpx.Gpx(f"{TEST_PATH}/test_cases/no_read_permission.gpx")
    assert route._load_file() is None


def test_to_dict():
    route = gpx.Gpx(f"{TEST_PATH}/test_cases/basic_sample.gpx")
    route_dict = route.to_dict()

    # Extract data to check
    first = [route_dict["lat"][0], route_dict["lon"][0],
             route_dict["ele"][0]]
    last = [route_dict["lat"][-1], route_dict["lon"][-1],
            route_dict["ele"][-1]]

    # Insert time in an easy-to-compare format
    first_time = route_dict["time"][0]
    first.append(dt.datetime(first_time.year, first_time.month,
                             first_time.day, first_time.hour,
                             first_time.minute, first_time.second))

    last_time = route_dict["time"][-1]
    last.append(dt.datetime(last_time.year, last_time.month,
                            last_time.day, last_time.hour,
                            last_time.minute, last_time.second))

    # Reference data
    first_ref = [46.2406490, 6.0342000, 442.0,
                 dt.datetime(2015, 7, 24, 6, 44, 14)]
    last_ref = [46.2301180, 6.0525330, 428.2,
                dt.datetime(2015, 7, 24, 6, 52, 24)]

    # Compare lists with reference and read data
    assert all([a == b for a, b in zip(first + last, first_ref + last_ref)])


@pytest.mark.xfail
def test_to_pandas():
    assert fail()


@pytest.mark.xfail
def test_write():
    assert fail()
