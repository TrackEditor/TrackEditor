import pandas as pd
import numpy as np
import datetime as dt
import geopy.distance
import gpxpy.gpx
from src import utils, gpx
from src import constants as c


class Track:
    def __init__(self):
        # Define dataframe and types
        self.columns = ['lat', 'lon', 'ele', 'segment', 'time']
        self.df_track = pd.DataFrame(columns=self.columns)
        self.df_track['lat'] = self.df_track['lat'].astype('float64')
        self.df_track['lon'] = self.df_track['lon'].astype('float64')
        self.df_track['ele'] = self.df_track['ele'].astype('float64')
        self.df_track['segment'] = self.df_track['segment'].astype('int64')
        self.df_track['time'] = self.df_track['time'].astype('datetime64[ns]')

        # General purpose properties
        self.size = 0  # number of gpx in track
        self.last_index = 0
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
            self.last_index += 1
            df_gpx['segment'] = self.last_index

            self.df_track = pd.concat([self.df_track, df_gpx])
            self.df_track = self.df_track.reset_index(drop=True)
            self._update_summary()  # for full track

    def _update_summary(self):
        self._insert_positive_elevation()
        self._insert_negative_elevation()
        self._insert_distance()
        self._update_extremes()
        self.total_distance = self.df_track.distance.iloc[-1]
        self.total_uphill = self.df_track.ele_pos_cum.iloc[-1]
        self.total_downhill = self.df_track.ele_neg_cum.iloc[-1]

    def get_segment(self, index: int):
        return self.df_track[self.df_track['segment'] == index]

    def reverse_segment(self, index: int):
        segment = self.get_segment(index)
        rev_segment = pd.DataFrame(segment.values[::-1].astype('float32'),
                                   segment.index,
                                   segment.columns)
        self.df_track.loc[self.df_track['segment'] == index] = rev_segment
        self._update_summary()  # for full track

    def insert_timestamp(self, initial_time, speed):
        self.df_track['time'] = \
            self.df_track.apply(
                lambda row: initial_time +
                            dt.timedelta(hours=row['distance']/speed),
                axis=1)

    def _insert_positive_elevation(self):
        self.df_track['ele diff'] = self.df_track['ele'].diff()
        negative_gain = self.df_track['ele diff'] < 0
        self.df_track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.df_track['ele_pos_cum'] = \
            self.df_track['ele diff'].cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(labels=['ele diff'], axis=1)

    def _insert_negative_elevation(self):
        self.df_track['ele diff'] = self.df_track['ele'].diff()
        negative_gain = self.df_track['ele diff'] > 0
        self.df_track.loc[negative_gain, 'ele diff'] = 0

        # Define new column
        self.df_track['ele_neg_cum'] = \
            self.df_track['ele diff'].cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(labels=['ele diff'], axis=1)

    def _insert_distance(self):
        # Shift latitude and longitude (such way that first point is 0km)
        self.df_track['lat_shift'] = pd.concat(
            [pd.Series(np.nan), self.df_track.lat[0:-1]]).\
            reset_index(drop=True)
        self.df_track['lon_shift'] = pd.concat(
            [pd.Series(np.nan), self.df_track.lon[0:-1]]).\
            reset_index(drop=True)

        def compute_distance(row):
            from_coor = (row.lat, row.lon)
            to_coor = (row.lat_shift, row.lon_shift)
            try:
                return abs(geopy.distance.geodesic(from_coor, to_coor).km)
            except ValueError:
                return 0

        # Define new columns
        self.df_track['p2p_distance'] = self.df_track.apply(compute_distance,
                                                            axis=1)
        self.df_track['distance'] = \
            self.df_track.p2p_distance.cumsum().astype('float32')

        # Drop temporary columns
        self.df_track = self.df_track.drop(
            labels=['lat_shift', 'lon_shift', 'p2p_distance'], axis=1)

    def _update_extremes(self):
        self.extremes = \
            (self.df_track["lat"].min(), self.df_track["lat"].max(),
             self.df_track["lon"].min(), self.df_track["lon"].max())

    def save_gpx(self, gpx_filename: str):
        # Create track
        ob_gpxpy = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        ob_gpxpy.tracks.append(gpx_track)

        # Create segments in track
        for seg_id in self.df_track.segment.unique():
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            df_segment = self.get_segment(seg_id)

            # Insert points to segment
            for idx in df_segment.index:
                latitude = df_segment.loc[idx, 'lat']
                longitude = df_segment.loc[idx, 'lon']
                elevation = df_segment.loc[idx, 'ele']
                time = df_segment.loc[idx, 'time']
                gpx_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude,
                                                    elevation=elevation,
                                                    time=time)
                gpx_segment.points.append(gpx_point)

        # Write file
        with open(gpx_filename, 'w') as f:
            f.write(ob_gpxpy.to_xml())

    def fix_elevation(self, index: int):
        df_segment = self.get_segment(index)

        # Identify and remove steep zones
        steep_zone = [False] * df_segment.shape[0]
        last_steep = 0

        for i, (e, d) in enumerate(zip(df_segment['ele'].diff(),
                                       df_segment['distance'])):
            if abs(e) > c.steep_gap:
                steep_zone[i] = True
                last_steep = d

            elif d - last_steep < c.steep_distance:
                if d > c.steep_distance:
                    steep_zone[i] = True

        df_segment['steep_zone'] = steep_zone
        df_no_steep = df_segment.copy()
        df_no_steep['ele_to_fix'] = np.where(df_segment['steep_zone'] == False,
                                             df_segment['ele'], -1)

        # Fill steep zones
        fixed_elevation = df_no_steep['ele_to_fix'].to_numpy()
        original_elevation = df_no_steep['ele'].to_numpy()
        fixed_steep_zone = df_no_steep['steep_zone']
        before_x = before_y = after_x = after_y = None  # initialization

        for i in range(1, len(fixed_elevation)):
            if not df_no_steep['steep_zone'].loc[i - 1] and \
                    df_no_steep['steep_zone'].loc[i]:
                before_x = np.arange(i - 11, i - 1)
                before_y = fixed_elevation[i - 11:i - 1]
                after_x = None
                after_y = None

            if df_no_steep['steep_zone'].loc[i - 1] and not \
                    df_no_steep['steep_zone'].loc[i]:
                after_x = np.arange(i, i + 10)
                after_y = fixed_elevation[i:i + 10]
                coef = np.polyfit(np.concatenate((before_x, after_x)),
                                  np.concatenate((before_y, after_y)),
                                  3)
                for j in range(before_x[-1], after_x[0]):
                    fixed_elevation[j] = np.polyval(coef, j)
                    fixed_steep_zone[j] = False

        if not after_y and not after_x and before_x and before_y:
            n = c.steep_k_moving_average
            fixed_elevation[before_x[-1]:] = np.concatenate((
                original_elevation[before_x[-1]:before_x[-1] + n - 1],
                utils.moving_average(original_elevation[before_x[-1]:], n)))
            fixed_steep_zone[before_x[-1]:] = True

        # Insert new elevation in track
        df_segment['ele'] = fixed_elevation
        self.df_track.loc[self.df_track['segment'] == index] = df_segment

    def remove_segment(self, index: int):
        # Drop rows in dataframe
        idx_segment = self.df_track[(self.df_track['segment'] == index)].index
        self.df_track = self.df_track.drop(idx_segment)
        self.df_track = self.df_track.reset_index(drop=True)
        self.size -= 1

        # Update metadata
        self._update_summary()
        self.loaded_files[index-1] = None

        # Clean full track if needed
        if self.size == 0:
            self.df_track = self.df_track.drop(self.df_track.index)

        return self.size

    def divide_segment(self, segment_index: int, div_index: int):
        self.df_track['index'] = self.df_track.index

        def segment_index_modifier(row):
            if row['segment'] < segment_index:
                return row['segment']
            elif row['segment'] > segment_index:
                return row['segment'] + 1
            else:
                if row['index'] < div_index:
                    return row['segment']
                else:
                    return row['segment'] + 1

        self.df_track['segment'] = \
            self.df_track.apply(lambda row: segment_index_modifier(row),
                                axis=1)

        self.df_track = self.df_track.drop(['index'], axis=1)

        return True

    def change_order(self, new_order: dict):
        self.df_track.segment = self.df_track.apply(
            lambda row: new_order[row.segment],
            axis=1)

        self.df_track['index1'] = self.df_track.index
        self.df_track = self.df_track.sort_values(by=['segment', 'index1'])
        self.df_track = self.df_track.drop(labels=['index1'], axis=1)
        self.df_track = self.df_track.reset_index(drop=True)
        self._update_summary()  # for full track
