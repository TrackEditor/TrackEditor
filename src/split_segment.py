from bisect import bisect
import pandas as pd

import plots


class SplitSegment:
    def __init__(self, shared_data, df_segment: pd.DataFrame):
        # Input data properties
        self.shared_data = shared_data
        self.df_segment = df_segment
        self.segment_idx = self.df_segment.segment.iloc[0]  # idx selected seg
        self.max_index = df_segment.index[-1]  # last index in dataframe
        self.ax = [shared_data.ax_track, shared_data.ax_ele]
        self.track = shared_data.obj_track
        self.canvas = shared_data.canvas

        # Prepare initial plot for splitting option
        self.vline, self.filled_area, self.ele_line, self.point = \
            self.initial_plot()

        # Extra properties
        self.index = 0  # variable to play with dataframe index
        self.press = None
        self.cidpress = None
        self.cidrelease = None
        self.cidmotion = None

    def initial_plot(self):
        """
        Create to different segments and a vertical line which will be moved
        to adapt sub-segment length.
        Help for output:
            - vline: vertical line which will be denote the splitting point in
                elevation plot
            - point: will be display in map corresponding to vline point
            - line, area: change color to visualize each new segment
        """

        # Common objects management
        ax_ele = self.shared_data.ax_ele

        # Create plot and establish interaction
        plots.plot_elevation(self.shared_data.obj_track,
                             self.shared_data.ax_ele,
                             selected_segment_idx=self.segment_idx)

        area = ax_ele.fill_between(self.df_segment.distance,
                                   self.df_segment.ele,
                                   color='b', alpha=0.2)
        line = ax_ele.plot(self.df_segment.distance, self.df_segment.ele,
                           color='b', linewidth=2)

        vline = ax_ele.axvline(self.df_segment.distance.iloc[0], linewidth=2)

        point = self.shared_data.ax_track.scatter(
            self.df_segment.lon.iloc[0], self.df_segment.lat.iloc[0],
            s=35, marker='o', c='r', zorder=20)

        # Enable button
        self.shared_data.btn_done.label._text = 'Done'
        self.shared_data.btn_done.hovercolor = '0.95'
        self.shared_data.btn_done.label._color = '0.05'

        self.shared_data.fig_track.canvas.draw()
        self.shared_data.fig_ele.canvas.draw()

        return vline, [area, None], [line, None], point

    def connect(self):
        """connect to all the events we need"""
        self.cidpress = self.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)
        # These prints are needed to work. They produce an exception, but
        # they make this utility to work for some reason...
        print(f'cidpress: {cidpress}')

    def on_press(self, event):
        """on button press we will see if the mouse is over us and store some
        data"""
        if event.inaxes != self.vline.axes:
            return

        contains, attrd = self.vline.contains(event)
        if not contains:
            return

        x0 = self.vline.get_xdata()[0]

        self.press = x0, event.xdata

    def on_motion(self, event):
        """on motion we will move the rect if the mouse is over us"""
        if self.press is None:
            return

        if event.inaxes != self.vline.axes:
            return

        x0, xpress = self.press
        dx = event.xdata - xpress

        # Move objects
        distance = self.df_segment.distance
        first_index = distance.index[0]
        self.index = bisect(distance.reset_index(drop=True), x0 + dx) + \
                     first_index

        if self.index < 0:
            self.index = 0
        elif self.index > self.max_index:
            self.index = self.max_index

        self.vline.set_xdata(2 * [distance[self.index]])

        # Update position
        try:
            self.point.remove()
        except Exception as e:
            print(e)

        self.point = self.ax[0].scatter(self.df_segment.lon[self.index],
                                        self.df_segment.lat[self.index],
                                        s=35, marker='o', c='r', zorder=20)

        # Update elevation
        try:
            self.ele_line[0][0].remove()
            self.ele_line[1][0].remove()
            self.filled_area[0].remove()
            self.filled_area[1].remove()
        except (IndexError, TypeError) as e:
            print(e)

        self.ele_line[0] = self.ax[1].plot(
            self.df_segment.distance.loc[:self.index+1],
            self.df_segment.ele.loc[:self.index+1],
            color='r', linewidth=2)
        self.ele_line[1] = self.ax[1].plot(
            self.df_segment.distance.loc[self.index:],
            self.df_segment.ele.loc[self.index:],
            color='b', linewidth=2)

        self.filled_area[0] = self.ax[1].fill_between(
            self.df_segment.distance.loc[:self.index],
            self.df_segment.ele.loc[:self.index],
            color='r', alpha=0.2)
        self.filled_area[1] = self.ax[1].fill_between(
            self.df_segment.distance.loc[self.index:],
            self.df_segment.ele.loc[self.index:],
            color='b', alpha=0.2)

        self.canvas.draw()

    def on_release(self, event):
        """on release we reset the press data"""

        self.press = None

        def divide_segment(_event):
            self.track.divide_segment(self.index)
            self.disconnect()

            # Update plot
            plots.plot_track(self.shared_data.obj_track,
                             self.shared_data.ax_track)
            plots.plot_track_info(
                self.shared_data.obj_track,
                self.shared_data.ax_track_info)

            plots.plot_elevation(self.shared_data.obj_track,
                                 self.shared_data.ax_ele)

        self.shared_data.btn_done.on_clicked(divide_segment)

        self.canvas.draw()

    def disconnect(self):
        """disconnect all the stored connection ids"""
        # Disable button
        self.shared_data.btn_done._text = '$Done$'
        self.shared_data.btn_done.hovercolor = self.shared_data.btn_done.color
        self.shared_data.btn_done.label._color = '0.6'

        # Disconnect
        self.canvas.mpl_disconnect(self.cidpress)
        self.canvas.mpl_disconnect(self.cidrelease)
        self.canvas.mpl_disconnect(self.cidmotion)
