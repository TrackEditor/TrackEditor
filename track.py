import pandas as pd
import geopy.distance

import gpx
import utils


class Track:
    def __init__(self):
        self.columns = ['lat', 'lon', 'ele', 'segment']
        self.track = pd.DataFrame(columns=self.columns)
        self.size = 0  # number of gpx in track
        self.extremes = (0, 0, 0, 0)  # lat min, lat max, lon min, lon max
        self.total_distance = 0
        self.loaded_files = []  # md5 of files in Track

    def add_gpx(self, file: str):
        md5_gpx = utils.md5sum(file)

        if md5_gpx not in self.loaded_files:
            gpx_track = gpx.Gpx(file)
            df_gpx = gpx_track.to_pandas()
            df_gpx = df_gpx[self.columns]
            self.loaded_files.append(md5_gpx)
            self.size += 1

            df_gpx['segment'] = self.size

            self.track = pd.concat([self.track, df_gpx])
            self.track = self.track.reset_index(drop=True)
            self._insert_positive_elevation()  # for full track
            self._insert_distance()  # for full track
            self._update_extremes()
            self.total_distance = self.track.distance.iloc[-1]

    def get_segment(self, index: int):
        return self.track[self.track['segment'] == index]

    def _insert_positive_elevation(self):
        self.track['ele diff'] = self.track['ele'].diff()
        negative_gain = self.track['ele diff'] < 0
        self.track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.track['ele_pos_cum'] = self.track['ele diff'].cumsum()

        # Drop temporary columns
        self.track = self.track.drop(labels=['ele diff'], axis=1)

    def _insert_distance(self):
        # Shift latitude and longitude
        self.track['lat_shift'] = self.track.lat[1:].reset_index(drop=True)
        self.track['lon_shift'] = self.track.lon[1:].reset_index(drop=True)

        def compute_distance(row):
            from_coor = (row.lat, row.lon)
            to_coor = (row.lat_shift, row.lon_shift)
            try:
                return abs(geopy.distance.geodesic(from_coor, to_coor).km)
            except ValueError:
                return 0

        # Define new columns
        self.track['p2p_distance'] = self.track.apply(compute_distance,
                                                      axis=1)
        self.track['distance'] = self.track.p2p_distance.cumsum()

        # Drop temporary columns
        self.track = self.track.drop(
            labels=['lat_shift', 'lon_shift', 'p2p_distance'], axis=1)

    def _update_extremes(self):
        self.extremes = (self.track["lat"].min(), self.track["lat"].max(),
                         self.track["lon"].min(), self.track["lon"].max())
