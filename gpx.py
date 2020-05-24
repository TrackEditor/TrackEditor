import gpxpy
import pandas as pd
import os
import numpy as np
import datetime as dt

import constants as c


class NoPreviousGpx(Exception):
    pass


class Gpx:
    def __init__(self, file):
        # Private attributes
        self._filename = os.path.basename(file)
        self._filepath = os.path.abspath(file)
        self._state = False
        self._gpx = self._load_file()
        self._gpx_dict = None

        # Public attributes
        self.df = None

    def _check_state(self):
        if not self._state:
            msg = f"No gpx has been loaded. " + \
                  f"For developers: self._state is not True"
            raise NoPreviousGpx(msg)

        else:
            return True

    def _load_file(self):
        if os.stat(self._filepath).st_size < c.maximum_file_size:
            try:
                gpx_file = open(self._filepath, 'r')
                self._state = True
                return gpxpy.parse(gpx_file)

            except PermissionError:
                self._state = False
                return None

        else:
            self._state = False
            return None

    def to_dict(self):
        if not self._check_state():
            return {}

        self._gpx_dict = {"lat": [], "lon": [], "ele": [], "time": [],
                          "track": [], "segment": []}

        n_tracks = len(self._gpx.tracks)
        n_segments = [len(track.segments) for track in self._gpx.tracks]
        n_points = [[segment.points for segment in track.segments]
                    for track in self._gpx.tracks]

        for i_track in range(n_tracks):
            for i_seg in range(n_segments[i_track]):
                for i_point in \
                        self._gpx.tracks[i_track].segments[i_seg].points:
                    # TODO: implement corner case in which one gpx has missing information
                    self._gpx_dict["lat"].append(i_point.latitude)
                    self._gpx_dict["lon"].append(i_point.longitude)
                    self._gpx_dict["ele"].append(i_point.elevation)
                    self._gpx_dict["time"].append(i_point.time)  # This is
                    # datetime.datetime format
                    self._gpx_dict["track"].append(i_seg)
                    self._gpx_dict["segment"].append(i_track)
        return self._gpx_dict

    def to_pandas(self):
        if not self._gpx_dict:
            self.to_dict()

        self.df = pd.DataFrame(self._gpx_dict,
                               columns=['lat', 'lon', 'ele',
                                        'time', 'track', 'segment'])
        self.df["time"] = self.df["time"].values.astype(np.datetime64)
        return self.df.copy()

    def write(self):
        # TODO
        pass
