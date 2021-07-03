"""CONSTANTS

Author: alguerre
License: MIT
"""
import logging
import os

# gpx file parser options
maximum_file_size = 10e+6

# plot options
max_zoom = 16
map_size = 2  # number of tiles
margin_outbounds = 0  # extra tiles to load
max_displayed_points = 100

# fix elevation
steep_distance = 0.2  # steep zone is always longer than X m
steep_gap = 0.6  # threshold to consider a steep zone in elevation
steep_k_moving_average = 20  # step for moving average if needed
fix_thr = 1000  # under 1000 points smoothing is used instead of fixing

# log options
log_level = logging.DEBUG

# location
src_path = os.path.dirname(os.path.realpath(__file__))
prj_path = os.path.dirname(src_path)
test_path = os.path.dirname(src_path) + '/test'
db_path = 'db_track_editor.sqlite'
db_test_path = test_path + '/db_test.sqlite'
ico_path = prj_path + '/media/compass.ico'
xbm_path = prj_path + '/media/compass.xbm'

# OSM request options
version = "v0.12"
email = "alguerre@outlook.com"
tool = "TrackEditor"

# gpx metadata
device = "Garmin Edge 830"
author_email = email
author_name = "Alonso Guarrior"
description = f"This activity has been updated with {tool} {version}"
