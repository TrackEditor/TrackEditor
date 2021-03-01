import pytest
import pandas as pd
import numpy as np
import datetime as dt

import track
from constants import prj_path

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def test_add_gpx():
    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Check that the file is properly loaded
    assert obj_track.df_track.lat.iloc[0] == -37.309450000000005
    assert obj_track.df_track.lon.iloc[0] == -12.696700000000002
    assert obj_track.df_track.ele.iloc[0] == 537.61
    assert obj_track.df_track.lat.iloc[-1] == -37.30682
    assert obj_track.df_track.lon.iloc[-1] == -12.697750000000001
    assert obj_track.df_track.ele.iloc[-1] == 550.0200000000001
    assert obj_track.df_track.shape[0] == 141


def test_update_summary():
    """
    Private method test: executed within add_gpx
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')

    # Initial data
    total_distance = obj_track.total_distance
    total_uphill = obj_track.total_uphill
    total_downhill = obj_track.total_downhill

    # Force to update summary
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part2.gpx')

    # Check that every summary number is updated
    assert total_distance != obj_track.total_distance
    assert total_uphill != obj_track.total_uphill
    assert total_downhill != obj_track.total_downhill


def test_insert_positive_elevation():
    """
    Private method test: executed within add_gpx
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Overall initial information
    total_pos_elevation = obj_track.df_track.ele_pos_cum.iloc[-1]

    assert total_pos_elevation == pytest.approx(909.71997)


def test_insert_negative_elevation():
    """
    Private method test: executed within add_gpx
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Overall initial information
    total_neg_elevation = obj_track.df_track.ele_neg_cum.iloc[-1]

    assert total_neg_elevation == pytest.approx(-897.31000)


def test_insert_distance():
    """
    Private method test: executed within add_gpx
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Overall initial information
    total_distance = obj_track.df_track.distance.iloc[-1]

    assert total_distance == pytest.approx(12.121018)


def test_update_extremes():
    """
    Private method test: executed within add_gpx
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')

    # Get reference data
    extremes = obj_track.extremes

    # Load more data
    for i in range(2, 6):
        obj_track.add_gpx(
            f'{prj_path}/test/test_cases/Innacessible_Island_part{i}.gpx')

    new_extremes = obj_track.extremes

    assert not (new_extremes == extremes)
    assert new_extremes[0] == pytest.approx(obj_track.df_track["lat"].min())
    assert new_extremes[1] == pytest.approx(obj_track.df_track["lat"].max())
    assert new_extremes[2] == pytest.approx(obj_track.df_track["lon"].min())
    assert new_extremes[3] == pytest.approx(obj_track.df_track["lon"].max())


def test_reverse_segment():
    """
    Verify that lat, lon and ele are properly inverted. Total distance is not
    applicable since this operation can provoke a change.
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')

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
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

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
    assert obj_track.size == 2


def test_multi_divide_segment():
    """
    Split the segment at different indexes and check that the segment id
    is properly updated
    """

    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

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
    assert obj_track.size == 4


def test_change_order():
    """
    Check that the order has been properly changed by looking at first and
    last row elements of the segment.
    """

    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part2.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part3.gpx')

    # Get initial data
    init_segment = {}
    end_segment = {}
    for i in range(3):
        seg_idx = i+1
        segment = obj_track.get_segment(seg_idx)
        init_segment[seg_idx] = {'lat': segment.iloc[0].lat,
                                 'lon': segment.iloc[0].lon,
                                 'ele': segment.iloc[0].ele}
        end_segment[seg_idx] = {'lat': segment.iloc[-1].lat,
                                'lon': segment.iloc[-1].lon,
                                'ele': segment.iloc[-1].ele}

    # Apply function
    new_order = {1: 3, 2: 1, 3: 2}
    obj_track.change_order(new_order)

    # Checks
    for i in new_order:
        new_i = new_order[i]
        old_i = i
        segment = obj_track.get_segment(new_i)  # after the re-ordering

        assert init_segment[old_i]['lat'] == pytest.approx(segment.iloc[0].lat)
        assert init_segment[old_i]['lon'] == pytest.approx(segment.iloc[0].lon)
        assert init_segment[old_i]['ele'] == pytest.approx(segment.iloc[0].ele)
        assert end_segment[old_i]['lat'] == pytest.approx(segment.iloc[-1].lat)
        assert end_segment[old_i]['lon'] == pytest.approx(segment.iloc[-1].lon)
        assert end_segment[old_i]['ele'] == pytest.approx(segment.iloc[-1].ele)


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
    obj_track = load_session(f'{prj_path}/test/test_cases/kungsleden.h5')

    # Get initial data
    initial_std = np.std(obj_track.df_track.ele)
    initial_max_peak = max(obj_track.df_track.ele)

    # Apply function
    obj_track.fix_elevation(1)

    final_std = np.std(obj_track.df_track.ele)
    final_max_peak = max(obj_track.df_track.ele)

    assert initial_max_peak > final_max_peak
    assert initial_std > final_std


def test_smooth_elevation():
    """
    The established criteria is to check that the standard deviation and
    maximum peak are lower than at the beggining.
    """
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Get initial data
    initial_std = np.std(obj_track.df_track.ele)
    initial_max_peak = max(obj_track.df_track.ele)

    # Apply function
    obj_track.smooth_elevation(1)

    final_std = np.std(obj_track.df_track.ele)
    final_max_peak = max(obj_track.df_track.ele)

    assert initial_max_peak > final_max_peak
    assert initial_std > final_std


def test_remove_segment():
    """
    Remove one segment and check that it is not available after the removal
    """
    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part2.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part3.gpx')

    # Apply method
    obj_track.remove_segment(2)

    # Check
    assert 2 not in obj_track.df_track.segment.unique()


def test_get_segment():
    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part1.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part2.gpx')
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_part3.gpx')

    # Reference segment
    ref_df = obj_track.df_track[obj_track.df_track.segment == 2].copy()

    # Get segment 2
    seg_df = obj_track.get_segment(2)

    # Compare segment 2 and copy
    # Take care of NaN since np.nan == np.nan is false
    assert (ref_df.fillna(0) == seg_df.fillna(0)).all().all()


def datetime_to_integer(dt_time):
    return 3600*24*dt_time.days + dt_time.seconds


def test_insert_timestamp():
    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Apply method
    initial_time = dt.datetime(2010, 1, 1)
    obj_track.insert_timestamp(initial_time, 1.0)

    # Checks
    assert not obj_track.df_track.time.isnull().values.any()  # no NaN
    assert obj_track.df_track.time.iloc[0] == initial_time
    assert all(x > 0 for x in
               list(map(datetime_to_integer,
                        obj_track.df_track.time.diff().to_list()))[1:])
    # timestamp is increasing


def test_columns_type():
    # Load data
    obj_track = track.Track()

    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Apply method
    obj_track._columns_type()

    # Checks
    types = obj_track.df_track.dtypes
    assert types.lat == np.float32
    assert types.lon == np.float32
    assert types.ele == np.float32
    assert types.segment == np.int32
    assert str(types.time) == 'datetime64[ns]'


def test_save_gpx():
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx(
        f'{prj_path}/test/test_cases/Innacessible_Island_Full.gpx')

    # Insert timestamp, no timestamp is checked in file_menu.py wrapper
    initial_time = dt.datetime(2010, 1, 1)
    obj_track.insert_timestamp(initial_time, 1.0)

    # Apply method
    filename = f'test_save_gpx_{np.random.randint(1e+6 - 1, 1e+6)}.gpx'
    obj_track.save_gpx(filename)

    # Load saved file
    saved_track = track.Track()
    saved_track.add_gpx(filename)

    # Check
    assert (obj_track.df_track.fillna(0) ==
            saved_track.df_track.fillna(0)).all().all()
