import pandas as pd
import numpy as np
import geopy.distance
import gpxpy.gpx
from src import utils, gpx


class Track:
    def __init__(self):
        self.columns = ['lat', 'lon', 'ele', 'segment']
        self.track = pd.DataFrame(columns=self.columns)
        self.size = 0  # number of gpx in track
        self.extremes = (0, 0, 0, 0)  # lat min, lat max, lon min, lon max
        self.total_distance = 0
        self.total_uphill = 0
        self.total_downhill = 0
        self.loaded_files = []  # md5 of files in Track
        self.selected_segment = []  # line object from matplotlib
        self.selected_segment_idx = []  # index of the segment

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
            self._update_summary()  # for full track

    def _update_summary(self):
        self._insert_positive_elevation()
        self._insert_negative_elevation()
        self._insert_distance()
        self._update_extremes()
        self.total_distance = self.track.distance.iloc[-1]
        self.total_uphill = self.track.ele_pos_cum.iloc[-1]
        self.total_downhill = self.track.ele_neg_cum.iloc[-1]

    def get_segment(self, index: int):
        return self.track[self.track['segment'] == index]

    def reverse_segment(self, index: int):
        print(self.track)
        segment = self.get_segment(index)
        rev_segment = pd.DataFrame(segment.values[::-1],
                                   segment.index,
                                   segment.columns)
        self.track.loc[self.track['segment'] == index] = rev_segment
        self._update_summary()  # for full track
        print(self.track)
        print('reverse_segment')

    def _insert_positive_elevation(self):
        self.track['ele diff'] = self.track['ele'].diff()
        negative_gain = self.track['ele diff'] < 0
        self.track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.track['ele_pos_cum'] = self.track['ele diff'].cumsum()

        # Drop temporary columns
        self.track = self.track.drop(labels=['ele diff'], axis=1)

    def _insert_negative_elevation(self):
        self.track['ele diff'] = self.track['ele'].diff()
        negative_gain = self.track['ele diff'] > 0
        self.track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.track['ele_neg_cum'] = self.track['ele diff'].cumsum()

        # Drop temporary columns
        self.track = self.track.drop(labels=['ele diff'], axis=1)

    def _insert_distance(self):
        # Shift latitude and longitude (such way that first point is 0km)
        self.track['lat_shift'] = pd.concat(
            [pd.Series(np.nan), self.track.lat[0:-1]]).\
            reset_index(drop=True)
        self.track['lon_shift'] = pd.concat(
            [pd.Series(np.nan), self.track.lon[0:-1]]).\
            reset_index(drop=True)

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

    def save_gpx(self, gpx_filename: str):
        # Create track
        ob_gpxpy = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        ob_gpxpy.tracks.append(gpx_track)

        # Create segments in track
        for seg_id in self.track.segment.unique():
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            df_segment = self.get_segment(seg_id)

            # Insert points to segment
            for idx in df_segment.index:
                latitude = df_segment.loc[idx, 'lat']
                longitude = df_segment.loc[idx, 'lon']
                elevation = df_segment.loc[idx, 'ele']
                gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude,
                                                    elevation=elevation)
                gpx_segment.points.append(gpx_point)

        # Write file
        with open(gpx_filename, 'w') as f:
            f.write(ob_gpxpy.to_xml())
