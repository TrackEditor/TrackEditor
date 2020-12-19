import datetime as dt
import tkinter as tk
import tkinter.messagebox as messagebox
import collections
import math
from bisect import bisect
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.widgets as widgets

import src.utils as utils
import src.plots as plots


INDEX = 0
MPL_BUTTON = None


class SplitInteraction:
    def __init__(self, vline, filled_area, ele_line, point, axes, df, canvas, track, controller):
        self.vline = vline
        self.filled_area = [filled_area, None]
        self.ele_line = [ele_line, None]
        self.point = point
        self.ax = axes
        self.df = df
        self.index = 0
        self.press = None
        self.cidpress = None
        self.cidrelease = None
        self.cidmotion = None
        self.canvas = canvas
        self.max_index = df.index[-1]
        self.track = track
        self.controller = controller

    def connect(self):
        """connect to all the events we need"""
        print('connection')
        self.cidpress = self.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

        print(f'cidpress: {cidpress}')
        print(f'cidrelease: {cidrelease}')
        print(f'cidmotion: {cidmotion}')

    def on_press(self, event):
        """on button press we will see if the mouse is over us and store some
        data"""
        print('on_press')
        if event.inaxes != self.vline.axes:
            print('leaves here: abc')
            return

        contains, attrd = self.vline.contains(event)
        if not contains:
            print('leaves here: def')
            return

        # print('event contains', self.rect.get_ydata())
        x0 = self.vline.get_xdata()[0]
        print(f'x0 = {x0}')
        self.press = x0, event.xdata

    def on_motion(self, event):
        """on motion we will move the rect if the mouse is over us"""
        # print('on_motion')
        if self.press is None:
            return

        if event.inaxes != self.vline.axes:
            return

        x0, xpress = self.press
        dx = event.xdata - xpress

        # Move objects
        distance = self.df.distance
        self.index = bisect(distance, x0 + dx)
        if self.index < 0:
            self.index = 0
        elif self.index > self.max_index:
            self.index = self.max_index
        print(self.index, x0, dx)

        self.vline.set_xdata(2 * [distance[self.index]])

        # Update position
        try:
            self.point.remove()
        except Exception as e:
            print(e)

        print(self.df.lat[self.index], self.df.lon[self.index])
        self.point = self.ax[0].scatter(self.df.lon[self.index],
                                        self.df.lat[self.index],
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
            self.df.distance[:self.index+1],
            self.df.ele[:self.index+1],
            color='r', linewidth=2)
        self.ele_line[1] = self.ax[1].plot(
            self.df.distance[self.index:],
            self.df.ele[self.index:],
            color='b', linewidth=2)

        self.filled_area[0] = self.ax[1].fill_between(
            self.df.distance[:self.index+1],
            self.df.ele[:self.index+1],
            color='r', alpha=0.2)
        self.filled_area[1] = self.ax[1].fill_between(
            self.df.distance[self.index:],
            self.df.ele[self.index:],
            color='b', alpha=0.2)

        self.canvas.draw()

    def on_release(self, event):
        """on release we reset the press data"""
        print('on_release')

        self.press = None

        def divide_segment(event):
            print('---divide_segment---')
            print(self.df.segment.iloc[0])
            print(self.index)
            self.track.divide_segment(self.df.segment.iloc[0], self.index)
            self.disconnect()

            # Update plot
            plots.plot_track(self.controller.shared_data.my_track,
                             self.controller.shared_data.ax_track)
            plots.plot_track_info(
                self.controller.shared_data.my_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.my_track,
                                 self.controller.shared_data.ax_ele)

        MPL_BUTTON.on_clicked(divide_segment)

        self.canvas.draw()

    def disconnect(self):
        """disconnect all the stored connection ids"""
        print('disconnect')
        self.canvas.mpl_disconnect(self.cidpress)
        self.canvas.mpl_disconnect(self.cidrelease)
        self.canvas.mpl_disconnect(self.cidmotion)


class EditMenu(tk.Menu):
    """
    Implements all the edition options for tracks: cut, reverse, insert time,
    split...
    """
    def __init__(self, parent, controller):
        # Define hinheritance
        tk.Menu.__init__(self, parent)
        self.controller = controller  # self from parent class
        self.parent = parent

        # Define menu
        self.editmenu = tk.Menu(parent, tearoff=0)
        self.editmenu.add_command(label='Reverse',
                                  command=self.reverse_segment)
        self.editmenu.add_command(label='Insert time',
                                  command=self.insert_time)
        self.editmenu.add_command(label='Fix elevation',
                                  command=self.fix_elevation)
        self.editmenu.add_command(label='Split segment',
                                  command=self.split_segment)
        self.editmenu.add_command(label='Remove segment',
                                  command=self.remove_segment)
        parent.add_cascade(label='Edit', menu=self.editmenu)

        # Time variables initialization
        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

    def reverse_segment(self):
        """
        Reverse order of data for the selected segment.
        """
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.my_track.reverse_segment(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.my_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.my_track,
                                 self.controller.shared_data.ax_ele)

            self.controller.shared_data.canvas.draw()

        elif len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')

    def insert_time(self):
        """
        Add time data to the whole track.
        Open a new window to introduce time and speed, then a timestamp is
        added to the whole track
        """
        if self.controller.shared_data.my_track.size == 0:
            message = 'There is no loaded track to insert timestamp'
            messagebox.showwarning(title='Insert Time Assistant',
                                   message=message)
            return

        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

        spinbox_options = {'year': [1990, 2030, 2000],
                           'month': [1, 12, 1],
                           'day': [1, 31, 1],
                           'hour': [0, 23, 0],
                           'minute': [0, 59, 0],
                           'second': [0, 59, 0]}

        top = tk.Toplevel()
        top.title('Insert Time Assistant')

        # Insert data frame
        frm_form = tk.Frame(top, relief=tk.FLAT, borderwidth=3)
        frm_form.pack()  # insert frame to use grid on it
        spn_time = collections.defaultdict()

        for i, entry in enumerate(spinbox_options):
            # This allow resize the window
            top.columnconfigure(i, weight=1, minsize=75)
            top.rowconfigure(i, weight=1, minsize=50)

            # Create widgets
            var = tk.StringVar(top)
            var.set(spinbox_options[entry][2])

            spn_time[entry] = tk.Spinbox(from_=spinbox_options[entry][0],
                                         to=spinbox_options[entry][1],
                                         master=frm_form,
                                         width=8,
                                         textvariable=var,
                                         justify=tk.RIGHT,
                                         relief=tk.FLAT)

            lbl_label = tk.Label(master=frm_form, text=f'{entry}', anchor='w')

            # Grid
            lbl_label.grid(row=i, column=0)  # grid attached to frame
            spn_time[entry].grid(row=i, column=1)

        # Insert speed
        i = len(spn_time)
        top.columnconfigure(i, weight=1, minsize=75)
        top.rowconfigure(i, weight=1, minsize=50)
        spn_speed = tk.Spinbox(from_=0, to=2000,
                               master=frm_form,
                               width=8,
                               justify=tk.RIGHT,
                               relief=tk.FLAT)
        lbl_label = tk.Label(master=frm_form, text=f'speed (km/h)', anchor='w')
        lbl_label.grid(row=i, column=0, pady=10)
        spn_speed.grid(row=i, column=1)

        def insert_timestamp():
            """
            Check input data and insert timestamp
            """
            try:
                self.timestamp = dt.datetime(int(spn_time['year'].get()),
                                             int(spn_time['month'].get()),
                                             int(spn_time['day'].get()),
                                             int(spn_time['hour'].get()),
                                             int(spn_time['minute'].get()),
                                             int(spn_time['second'].get()))
                self.speed = float(spn_speed.get())
                if self.speed <= 0:
                    raise ValueError('Speed must be a positive number.')

                # Insert timestamp
                self.controller.shared_data.my_track.\
                    insert_timestamp(self.timestamp, self.speed)
                top.destroy()

            except (ValueError, OverflowError) as e:
                messagebox.showerror('Input Error', e)

        def clear_box():
            for s in spn_time:
                spn_time[s].delete(0, 8)
                spn_time[s].insert(0, spinbox_options[s][2])
            spn_speed.delete(0, 8)
            spn_speed.insert(0, 0)

        # Button frame
        frm_button = tk.Frame(top)
        frm_button.pack(fill=tk.X, padx=5,
                        pady=5)  # fill in horizontal direction

        btn_clear = tk.Button(master=frm_button, text='Clear',
                              command=clear_box)
        btn_submit = tk.Button(master=frm_button, text='Submit',
                               command=insert_timestamp)
        btn_clear.pack(side=tk.RIGHT, padx=10)
        btn_submit.pack(side=tk.RIGHT, padx=10)

    def fix_elevation(self):
        """
        Apply the elevation correction on the selected segment.
        """
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.my_track.fix_elevation(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.my_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.my_track,
                                 self.controller.shared_data.ax_ele)

            self.controller.shared_data.canvas.draw()

        elif len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')

    def remove_segment(self):
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]

            msg = 'Do you want to remove the selected segment?'
            proceed = tk.messagebox.askyesno(title='Remove segment',
                                             message=msg)

            if proceed:
                size = self.controller.shared_data.my_track.remove_segment(
                    segment_idx)

                # Update plot
                if size > 0:
                    plots.plot_track_info(
                        self.controller.shared_data.my_track,
                        self.controller.shared_data.ax_track_info)

                    plots.plot_elevation(self.controller.shared_data.my_track,
                                         self.controller.shared_data.ax_ele)
                    plots.plot_track(self.controller.shared_data.my_track,
                                     self.controller.shared_data.ax_track)
                else:
                    plots.plot_world(self.controller.shared_data.ax_track)
                    plots.plot_no_elevation(self.controller.shared_data.ax_ele)
                    plots.plot_no_info(
                        self.controller.shared_data.ax_track_info)
                    tk.messagebox.showwarning(
                        title='No segment',
                        message='Last segment has been removed.')
                self.controller.shared_data.canvas.draw()

        elif len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')

    def split_segment(self):
        global MPL_BUTTON

        # Selection management
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
            return
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')
            return
        else:
            segment_idx = selected_segment[0]
            df_segment = \
                self.controller.shared_data.my_track.get_segment(segment_idx)

        # Common objects management
        ax_track = self.controller.shared_data.ax_track
        ax_ele = self.controller.shared_data.ax_ele
        canvas = self.controller.shared_data.canvas

        # canvas.mpl_disconnect(self.controller.shared_data.cid)
        # print(f'cid (edit_menu.py) ', self.controller.shared_data.cid)

        plots.plot_elevation(self.controller.shared_data.my_track,
                             self.controller.shared_data.ax_ele,
                             selected_segment_idx=segment_idx)

        area = ax_ele.fill_between(df_segment.distance, df_segment.ele,
                                   color='b', alpha=0.2)
        line = ax_ele.plot(df_segment.distance, df_segment.ele,
                           color='b', linewidth=2)

        _vline = ax_ele.axvline(df_segment.distance[0], linewidth=2)

        _point = self.controller.shared_data.ax_track.scatter(
            df_segment.lon[0], df_segment.lat[0],
            s=35, marker='o', c='r', zorder=20)

        button_position = plt.axes([0.8, 0.025, 0.1, 0.04])
        MPL_BUTTON = widgets.Button(button_position, 'Done', hovercolor='0.975')

        self.controller.shared_data.fig_track.canvas.draw()

        self.controller.shared_data.fig_ele.canvas.draw()

        interaction = SplitInteraction(_vline, area, line, _point,
                                       [ax_track, ax_ele], df_segment, canvas,
                                       self.controller.shared_data.my_track,
                                       self.controller)
        interaction.connect()
