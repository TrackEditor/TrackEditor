import logging

# gpx file parser options
maximum_file_size = 10e+6

# plot options
max_zoom = 16
map_size = 2  # number of tiles
margin_outbounds = 0  # extra tiles to load
click_distance = 0.25  # km TODO: this should be a function on zoom
max_displayed_points = 100

# fix elevation
steep_distance = 0.2  # steep zone is always longer than X m
steep_gap = 0.6  # threshold to consider a steep zone in elevation
steep_k_moving_average = 20  # step for moving average if needed

# log options
log_level = logging.DEBUG

# OSM request options
version = "v0.8"
email = "alguerre@outlook.com"
tool = "TrackEditor"

