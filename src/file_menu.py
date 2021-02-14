import os
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import pandas as pd
import types

import plots
import track
from utils import quit_app


class FileMenu(tk.Menu):
    """
    Implements basic options for direct manage of tracks such as loading/saving
    files or sessions.
    """
    def __init__(self, parent, controller):
        # Define hinheritance
        tk.Menu.__init__(self, parent)
        self.controller = controller  # self from parent class
        self.parent = parent

        # Define menu
        self.filemenu = tk.Menu(parent, tearoff=0)
        self.filemenu.add_command(label='Load track', command=self.load_track)
        self.filemenu.add_command(label='Load session',
                                  command=self.load_session)
        self.filemenu.add_command(label='New session',
                                  command=self.new_session)
        self.filemenu.add_command(label='Save session',
                                  command=self.save_session)
        self.filemenu.add_command(label='Save gpx',
                                  command=self.save_gpx)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit',
                                  command=lambda: quit_app(self.parent))
        parent.add_cascade(label='File', menu=self.filemenu)

    def load_track(self):
        # Load gpx file
        gpx_file = tk.filedialog.askopenfile(
            initialdir=os.getcwd(),
            title='Select gpx file',
            filetypes=[('Gps data file', '*.gpx'), ('All files', '*')])

        if gpx_file:  # user may close filedialog
            self.controller.shared_data.obj_track.add_gpx(gpx_file.name)

            # Insert plot
            plots.plot_track(self.controller.shared_data.obj_track,
                             self.controller.shared_data.ax_track)
            plots.plot_elevation(self.controller.shared_data.obj_track,
                                 self.controller.shared_data.ax_ele)
            track_info_table = plots.plot_track_info(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track_info)
            cid = plots.segment_selection(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track,
                self.controller.shared_data.ax_ele,
                self.controller.shared_data.fig_track,
                track_info_table)
            self.controller.shared_data.cid.append(cid)
            self.controller.shared_data.canvas.draw()

    def load_session(self):
        proceed = True

        if self.controller.shared_data.obj_track.size > 0:
            message = \
                'Current session will be deleted. Do you wish to proceed?'
            proceed = messagebox.askokcancel(title='Load session',
                                             message=message)

        if proceed:
            session_file = tk.filedialog.askopenfile(
                initialdir=os.getcwd(),
                title='Select session file',
                filetypes=[('Session file', '*.h5;*.hdf5;*he5'),
                           ('All files', '*')])
            if session_file:
                with pd.HDFStore(session_file.name) as store:
                    session_track = store['session']
                    session_meta = store.get_storer('session').attrs.metadata

                    # Load new track
                    self.controller.shared_data.obj_track.df_track = session_track
                    self.controller.shared_data.obj_track.loaded_files = \
                        session_meta.loaded_files
                    self.controller.shared_data.obj_track.size = \
                        session_meta.size
                    self.controller.shared_data.obj_track.total_distance = \
                        session_meta.total_distance
                    self.controller.shared_data.obj_track.extremes = \
                        session_meta.extremes

                    # Insert plot
                    plots.plot_track(self.controller.shared_data.obj_track,
                                     self.controller.shared_data.ax_track)
                    plots.plot_elevation(self.controller.shared_data.obj_track,
                                         self.controller.shared_data.ax_ele)
                    plots.plot_track_info(
                        self.controller.shared_data.obj_track,
                        self.controller.shared_data.ax_track_info)
                    self.controller.shared_data.canvas.draw()

    def new_session(self):
        proceed = True

        if self.controller.shared_data.obj_track.size > 0:
            message = \
                'Current session will be deleted. Do you wish to proceed?'
            proceed = messagebox.askokcancel(title='New session',
                                             message=message)

        if proceed:
            # Delete former objects
            del self.controller.shared_data.obj_track

            # Restart session
            self.controller.shared_data.obj_track = track.Track()

            # Plot
            plots.plot_world(self.controller.shared_data.ax_track)
            plots.plot_no_elevation(self.controller.shared_data.ax_ele)
            plots.plot_no_info(self.controller.shared_data.ax_track_info)

            # Stop interactivity
            for cid in self.controller.shared_data.cid:
                self.controller.shared_data.fig_track.canvas.mpl_disconnect(
                    cid)
            self.controller.shared_data.cid.clear()

            # Update plots
            self.controller.shared_data.canvas.draw()

    def save_session(self):
        session = self.controller.shared_data.obj_track.df_track

        metadata = types.SimpleNamespace()
        metadata.size = self.controller.shared_data.obj_track.size
        metadata.extremes = self.controller.shared_data.obj_track.extremes
        metadata.total_distance = \
            self.controller.shared_data.obj_track.total_distance
        metadata.loaded_files = \
            self.controller.shared_data.obj_track.loaded_files

        session_filename = tk.filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title='Save session as',
            filetypes=[('Session file', '*.h5')])

        if session_filename:  # user may close filedialog
            store = pd.HDFStore(session_filename)
            store.put('session', session)
            store.get_storer('session').attrs.metadata = metadata
            store.close()

    def save_gpx(self):
        if self.controller.shared_data.obj_track.df_track.time.isnull().any():
            msg = 'Timestamp is needed in order to generate your gpx.\n' + \
                  'Please, use Edit -> Insert Time'
            messagebox.showerror('Error', msg)
            return

        gpx_filename = tk.filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title='Save track as',
            filetypes=[('Gpx file', '*.gpx')])

        if gpx_filename:  # user may close filedialog
            self.controller.shared_data.obj_track.save_gpx(gpx_filename)

        messagebox.showinfo('Info', 'Your file is ready :)')
