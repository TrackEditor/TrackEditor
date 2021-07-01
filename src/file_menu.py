"""FILE_MENU
Definition of all the options of the File Menu in the GUI or Main Application.
The cascade menu is defined and each of the functionalities is provided.

Author: alguerre
License: MIT
"""
import os
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import pandas as pd
import types

import plots
import track
import utils


class FileMenu(tk.Menu):
    """
    Implements basic options for direct manage of tracks such as loading/saving
    files or sessions.
    """
    def __init__(self, parent, controller):
        # Define inheritance
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
                                  command=lambda: utils.quit_app(self.parent))
        parent.add_cascade(label='File', menu=self.filemenu)

    @utils.exception_handler
    def load_track(self):
        """
        Load a gpx file into the track object.
        """
        # Load gpx file
        gpx_file = filedialog.askopenfile(
            initialdir=os.getcwd(),
            title='Select gpx file',
            filetypes=[('Gps data file', '*.gpx'), ('All files', '*')])

        # def load_track_controller(gpx_file_name):
        #    self.controller.shared_data.obj_track.add_gpx(gpx_file_name)
        if gpx_file:  # user may close filedialog
            self.controller.shared_data.obj_track.add_gpx(gpx_file.name)

            # Insert plot
            track_info_table = plots.update_plots(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track,
                self.controller.shared_data.ax_ele,
                self.controller.shared_data.ax_track_info,
                canvas=self.controller.shared_data.canvas)

            cid = plots.segment_selection(
                self.controller.shared_data.obj_track,
                self.controller.shared_data.ax_track,
                self.controller.shared_data.ax_ele,
                self.controller.shared_data.fig_track,
                track_info_table)
            self.controller.shared_data.cid.append(cid)
            self.controller.shared_data.canvas.draw()

        # if gpx_file:  # user may close filedialog
        #     # load_track_controller(gpx_file.name)
        #     utils.execute_with_progressbar(self.parent,
        #                                    load_track_controller,
        #                                    gpx_file.name)


    @utils.exception_handler
    def load_session(self):
        """
        Load a .h5 file. This file has to be previously created with this same
        application, since it stores all the data as defined in save_session
        method.
        """
        proceed = True

        if self.controller.shared_data.obj_track.size > 0:
            message = \
                'Current session will be deleted. Do you wish to proceed?'
            proceed = messagebox.askokcancel(title='Load session',
                                             message=message)

        if proceed:
            session_file = filedialog.askopenfile(
                initialdir=os.getcwd(),
                title='Select session file',
                filetypes=[('Session file', '*.h5;*.hdf5;*he5'),
                           ('All files', '*')])
            if session_file:
                with pd.HDFStore(session_file.name) as store:
                    session_track = store['session']
                    session_meta = store.get_storer('session').attrs.metadata

                    # Load new track
                    self.controller.shared_data.obj_track.df_track = \
                        session_track
                    self.controller.shared_data.obj_track.size = \
                        session_meta.size
                    self.controller.shared_data.obj_track.total_distance = \
                        session_meta.total_distance
                    self.controller.shared_data.obj_track.total_uphill = \
                        session_meta.total_uphill
                    self.controller.shared_data.obj_track.total_downhill = \
                        session_meta.total_downhill
                    self.controller.shared_data.obj_track.last_segment_idx = \
                        session_meta.last_segment_idx
                    self.controller.shared_data.obj_track.extremes = \
                        session_meta.extremes

                    # Insert plot
                    track_info_table = plots.update_plots(
                        self.controller.shared_data.obj_track,
                        self.controller.shared_data.ax_track,
                        self.controller.shared_data.ax_ele,
                        self.controller.shared_data.ax_track_info,
                        canvas=self.controller.shared_data.canvas)

                    cid = plots.segment_selection(
                        self.controller.shared_data.obj_track,
                        self.controller.shared_data.ax_track,
                        self.controller.shared_data.ax_ele,
                        self.controller.shared_data.fig_track,
                        track_info_table)
                    self.controller.shared_data.cid.append(cid)
                    self.controller.shared_data.canvas.draw()

    @utils.exception_handler
    def new_session(self):
        """
        Remove all data and plots to start from scratch.
        """
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
            plots.initial_plots(
                self.controller.shared_data.ax_track,
                self.controller.shared_data.ax_ele,
                self.controller.shared_data.ax_track_info)

            # Stop interactivity
            for cid in self.controller.shared_data.cid:
                self.controller.shared_data.fig_track.canvas.mpl_disconnect(
                    cid)
            self.controller.shared_data.cid.clear()

            self.controller.shared_data.canvas.draw()  # draw updated plots

    @utils.exception_handler
    def save_session(self):
        """
        Save data in used in a .h5 file. This file can be loaded later on with
        the load_session method. All the information will be kept.
        """
        session = self.controller.shared_data.obj_track.df_track

        metadata = types.SimpleNamespace()
        metadata.size = self.controller.shared_data.obj_track.size
        metadata.extremes = self.controller.shared_data.obj_track.extremes
        metadata.total_distance = \
            self.controller.shared_data.obj_track.total_distance
        metadata.total_uphill = \
            self.controller.shared_data.obj_track.total_uphill
        metadata.total_downhill = \
            self.controller.shared_data.obj_track.total_downhill
        metadata.last_segment_idx = \
            self.controller.shared_data.obj_track.last_segment_idx

        session_filename = filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title='Save session as',
            filetypes=[('Session file', '*.h5')])

        if session_filename:  # user may close filedialog
            store = pd.HDFStore(session_filename)
            store.put('session', session)
            store.get_storer('session').attrs.metadata = metadata
            store.close()

        messagebox.showinfo('Info', 'Your session file is ready :)')

    @utils.exception_handler
    def save_gpx(self):
        """
        Save all data in used in a gpx file. This needs include timestamp
        information. No segments will be kept in the resulting file.
        """
        if self.controller.shared_data.obj_track.df_track.time.isnull().any():
            msg = 'Timestamp is needed in order to generate your gpx.\n' + \
                  'Please, use Edit -> Insert Time'
            messagebox.showerror('Error', msg)
            return

        gpx_filename = filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title='Save track as',
            filetypes=[('Gpx file', '*.gpx')])

        if gpx_filename:  # user may close filedialog
            self.controller.shared_data.obj_track.save_gpx(gpx_filename)

        messagebox.showinfo('Info', 'Your file is ready :)')
