import datetime as dt
import tkinter as tk
import tkinter.messagebox as messagebox
import collections

import plots
from split_segment import SplitSegment as SplitSegmentCallback


INDEX = 0
MPL_BUTTON = None


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
        self.editmenu.add_command(label='Change segment order',
                                  command=self.change_order)
        parent.add_cascade(label='Edit', menu=self.editmenu)

        # Time variables initialization
        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

    def reverse_segment(self):
        """
        Reverse order of data for the selected segment.
        """
        selected_segment = \
            self.controller.shared_data.obj_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.obj_track.reverse_segment(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_track(self.controller.shared_data.obj_track,
                             self.controller.shared_data.ax_track)

            plots.plot_elevation(self.controller.shared_data.obj_track,
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
        if self.controller.shared_data.obj_track.size == 0:
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
                self.controller.shared_data.obj_track.\
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
            self.controller.shared_data.obj_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.obj_track.fix_elevation(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.obj_track,
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
            self.controller.shared_data.obj_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]

            msg = 'Do you want to remove the selected segment?'
            proceed = tk.messagebox.askyesno(title='Remove segment',
                                             message=msg)

            if proceed:
                size = self.controller.shared_data.obj_track.remove_segment(
                    segment_idx)

                # Update plot
                if size > 0:
                    plots.plot_track_info(
                        self.controller.shared_data.obj_track,
                        self.controller.shared_data.ax_track_info)

                    plots.plot_elevation(self.controller.shared_data.obj_track,
                                         self.controller.shared_data.ax_ele)
                    plots.plot_track(self.controller.shared_data.obj_track,
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
        # Selection management
        selected_segment = \
            self.controller.shared_data.obj_track.selected_segment_idx

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
                self.controller.shared_data.obj_track.get_segment(segment_idx)

        # Create plot
        interaction = SplitSegmentCallback(
            self.controller.shared_data,
            df_segment)

        interaction.connect()

    def change_order(self):
        """
        change order
        """
        if self.controller.shared_data.obj_track.size == 0:
            message = 'There is no loaded track to change order'
            messagebox.showwarning(title='Insert Time Assistant',
                                   message=message)
            return

        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

        top = tk.Toplevel()
        top.title('Change Segment Order Assistant')

        # Insert data frame
        frm_form = tk.Frame(top, relief=tk.FLAT, borderwidth=3)
        frm_form.pack()  # insert frame to use grid on it
        spn_seg = collections.defaultdict()

        available_segments = \
            self.controller.shared_data.obj_track.df_track.segment.unique()

        for i, entry in enumerate(available_segments):
            # This allow resize the window
            top.columnconfigure(i, weight=1, minsize=75)
            top.rowconfigure(i, weight=1, minsize=50)

            # Create widgets
            var = tk.StringVar(top)
            var.set(i+1)
            color = plots.rgb2hexcolor(
                plots.color_rgb(plots.COLOR_LIST[(entry-1) % plots.N_COLOR]))

            spn_seg[entry] = tk.Spinbox(from_=1,
                                        to=99,
                                        master=frm_form,
                                        width=8,
                                        textvariable=var,
                                        justify=tk.RIGHT,
                                        relief=tk.FLAT)

            lbl_label = tk.Label(master=frm_form, text=f'{entry}', anchor='w',
                                 width=6,
                                 height=1,
                                 relief=tk.FLAT,
                                 justify=tk.CENTER,
                                 bg=color)

            # Grid
            lbl_label.grid(row=i, column=0)  # grid attached to frame
            spn_seg[entry].grid(row=i, column=1)

        # Button frame
        frm_button = tk.Frame(top)
        frm_button.pack(fill=tk.X, padx=5,
                        pady=5)  # fill in horizontal direction

        def clear_box():
            for i, s in enumerate(spn_seg):
                spn_seg[s].delete(0, 8)
                spn_seg[s].insert(0, i+1)
            spn_seg.insert(0, 0)

        def insert_order():

            # Check valid order
            new_order = {}
            for _entry in available_segments:
                new_order[_entry] = int(spn_seg[_entry].get())

            if len(set(new_order)) != len(available_segments):
                messagebox.showerror('Warning',
                                     'Invalid order. Repeated index.')
            elif max(new_order, key=int) != max(available_segments) or \
                    min(new_order, key=int) != min(available_segments):
                messagebox.showerror('Warning',
                                     'Invalid order. Bad max/min index.')
            else:
                self.controller.shared_data.obj_track.change_order(new_order)
                top.destroy()

                # Update plots
                plots.plot_elevation(self.controller.shared_data.obj_track,
                                     self.controller.shared_data.ax_ele)
                plots.plot_track(self.controller.shared_data.obj_track,
                                 self.controller.shared_data.ax_track)
                plots.plot_track_info(
                    self.controller.shared_data.obj_track,
                    self.controller.shared_data.ax_track_info)
                self.controller.shared_data.canvas.draw()

        btn_clear = tk.Button(master=frm_button, text='Clear',
                              command=clear_box)
        btn_submit = tk.Button(master=frm_button, text='Submit',
                               command=insert_order)
        btn_clear.pack(side=tk.RIGHT, padx=10)
        btn_submit.pack(side=tk.RIGHT, padx=10)
