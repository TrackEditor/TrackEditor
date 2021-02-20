import pytest
import os
import pandas as pd
import matplotlib.pyplot as plt

import track

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


@pytest.mark.skip(reason="To be reviewed")
def test_reverse_segment():
    pass


def test_divide_segment():
    """
    Split the segment in the index 100, before the segment id must be 1,
    at and after it must be 2.
    """

    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases/Innacessible_Island_Full.gpx')

    # Overal initial information
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
    Split the segment in the index 100, before the segment id must be 1,
    at and after it must be 2.
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
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

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


@pytest.mark.skip(reason="To be reviewed")
def test_fix_elevation():
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases\KUNGSLEDEN_Etapa_9_Kvikkjokk_Wild_Camping.gpx')

    obj_track.fix_elevation(0)
    plt.figure()
    plt.plot(obj_track.df_track.distance, obj_track.df_track.ele)
    plt.show()

    assert True
