import pytest
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import track

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def test_reverse_segment():
    """
    Verify that lat, lon and ele are properly inverted. Total distance is not
    applicable since this operation can provoke a change.
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases/Innacessible_Island_part1.gpx')

    # Overal initial information
    initial_shape = obj_track.df_track.shape

    # Copy for comparison
    lat_comp = obj_track.df_track.lat.copy().to_numpy().astype('float32')
    lon_comp = obj_track.df_track.lon.copy().to_numpy().astype('float32')
    ele_comp = obj_track.df_track.ele.copy().to_numpy().astype('float32')

    # Apply method
    obj_track.reverse_segment(1)

    # Specific checks
    assert np.all(obj_track.df_track.lat.to_numpy() ==
                  pytest.approx(lat_comp[::-1]))
    assert np.all(obj_track.df_track.lon.to_numpy() ==
                  pytest.approx(lon_comp[::-1]))
    assert np.all(obj_track.df_track.ele.to_numpy() ==
                  pytest.approx(ele_comp[::-1]))

    # Non-regression checks, total_distance is not applicable
    assert initial_shape == obj_track.df_track.shape


def test_divide_segment():
    """
    Split the segment in the index 100, before the segment id must be 1,
    at and after it must be 2.
    """

    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases/Innacessible_Island_Full.gpx')

    # Overall initial information
    initial_total_distance = obj_track.df_track.distance.iloc[-1]
    initial_shape = obj_track.df_track.shape

    # Apply method
    obj_track.divide_segment(100)

    # Specific checks
    assert obj_track.df_track.segment.iloc[99] == 1
    assert obj_track.df_track.segment.iloc[100] == 2

    # Non-regression checks
    assert initial_total_distance == obj_track.df_track.distance.iloc[-1]
    assert initial_shape == obj_track.df_track.shape


def test_multi_divide_segment():
    """
    Split the segment at different indexes and check that the segment id
    is properly updated
    """

    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases/Innacessible_Island_Full.gpx')

    # Overal initial information
    initial_total_distance = obj_track.df_track.distance.iloc[-1]
    initial_shape = obj_track.df_track.shape

    # Apply method
    obj_track.divide_segment(80)
    obj_track.divide_segment(120)
    obj_track.divide_segment(40)

    # # Specific checks
    assert obj_track.df_track.segment.iloc[39] == 1
    assert obj_track.df_track.segment.iloc[40] == 2
    assert obj_track.df_track.segment.iloc[80] == 3
    assert obj_track.df_track.segment.iloc[120] == 4
    assert obj_track.df_track.segment.iloc[-1] == 4

    # Non-regression checks
    assert initial_total_distance == obj_track.df_track.distance.iloc[-1]
    assert initial_shape == obj_track.df_track.shape


@pytest.mark.skip(reason="To be reviewed")
def test_change_order():

    check_points = {}

    # Load data
    obj_track = track.Track()

    check_points[0] = 1
    obj_track.add_gpx('test_cases/Innacessible_Island_part1.gpx')
    check_points[obj_track.df_track.index[-1]] = 1

    check_points[obj_track.df_track.index[-1] + 1] = 2
    obj_track.add_gpx('test_cases/Innacessible_Island_part2.gpx')
    check_points[obj_track.df_track.index[-1]] = 2

    check_points[obj_track.df_track.index[-1] + 1] = 3
    obj_track.add_gpx('test_cases/Innacessible_Island_part3.gpx')
    check_points[obj_track.df_track.index[-1]] = 3

    # Apply function
    new_order = {1: 3, 2: 1, 3: 2}
    obj_track.change_order(new_order)

    # Specific checks
    for cp in check_points:
        assert obj_track.df_track.segment.iloc[cp] == new_order[check_points[cp]]


def load_session(filename):
    """
    Load a .h5 session for a faster analysis
    """
    obj_track = track.Track()

    with pd.HDFStore(filename) as store:
        session_track = store['session']

        obj_track.df_track = session_track

    return obj_track


def test_fix_elevation():
    """
    The established criteria is to check that the standard deviation and
    maximum peak are lower than at the beggining.
    """
    # Load data
    obj_track = load_session('test_cases\kungsleden.h5')

    # Get initial data
    initial_std = np.std(obj_track.df_track.ele)
    initial_max_peak = max(obj_track.df_track.ele)

    # Apply function
    obj_track.fix_elevation(1)

    final_std = np.std(obj_track.df_track.ele)
    final_max_peak = max(obj_track.df_track.ele)

    assert initial_max_peak > final_max_peak
    assert initial_std > final_std
