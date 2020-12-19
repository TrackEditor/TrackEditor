import pytest
import os
import pandas as pd

from src import track


def test_divide_segment():
    # Load data
    obj_track = track.Track()
    obj_track.add_gpx('test_cases/Innacessible_Island_part1.gpx')
    obj_track.add_gpx('test_cases/Innacessible_Island_part2.gpx')
    obj_track.add_gpx('test_cases/Innacessible_Island_part3.gpx')

    # Overal initial information
    print(obj_track.track.distance.iloc[-1])
    initial_total_distance = obj_track.track.distance.iloc[-1]
    initial_shape = obj_track.track.shape

    # Apply method
    obj_track.divide_segment(2, 10)

    # General purpose checks
    assert initial_total_distance == obj_track.track.distance.iloc[-1]
    assert initial_shape == obj_track.track.shape

    # Specific checks
    assert obj_track.track.segment.iloc[24] == 2
    assert obj_track.track.segment.iloc[34] == 3
    assert obj_track.track.segment.iloc[47] == 4
