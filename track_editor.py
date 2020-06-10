import logging
import datetime as dt
import os
import tkinter as tk
# import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as backend_tkagg
# import matplotlib.backend_bases as backend_bases  # key_press_handler
# import matplotlib.figure as figure  # import Figure
# import numpy as np
import pandas as pd
import types
import plots

import track
import constants as c
# import iosm
# import utils


MY_TRACK = track.Track()


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.fig = plt.figure(figsize=(12, 8), dpi=100)
        self.ax_ele = None
        self.ax_track = None
        self.ax_track_info = None
        self.fig_ele = None
        self.fig_track = None
        self.fig_track_info = None
        self.canvas = backend_tkagg.FigureCanvasTkAgg(self.fig, self)
        self.my_track = track.Track()
        self.init_ui()  # Insert default image

        # Create menu
        self.menubar = tk.Menu(self.parent)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
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
        self.filemenu.add_command(label='Exit', command=self.quit_app)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.parent.config(menu=self.menubar)

        #  Insert navigation toolbar for plots
        toolbar = backend_tkagg.NavigationToolbar2Tk(self.canvas, root)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def init_ui(self):
        # Prepare plot grid distribution
        gspec = gridspec.GridSpec(4, 8)

        # Plot world map
        plt.subplot(gspec[:3, :5])
        self.ax_track = plt.gca()
        self.fig_track = plt.gcf()
        plots.plot_world(self.ax_track)

        # Plot fake elevation
        with plt.style.context('ggplot'):
            plt.subplot(gspec[3, :5])
            self.ax_ele = plt.gca()
            self.fig_ele = plt.gcf()
            plots.plot_no_elevation(self.ax_ele)

        # Text box
        plt.subplot(gspec[:3, 5:])
        self.ax_track_info = plt.gca()
        self.fig_track_info = plt.gcf()
        plots.plot_no_info(self.ax_track_info)

        self.canvas.get_tk_widget().pack(expand=True, fill='both')

    def quit_app(self):
        self.parent.quit()  # stops mainloop
        self.parent.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def load_track(self):
        # Load gpx file
        gpx_file = tk.filedialog.askopenfile(
            initialdir=os.getcwd(),
            title='Select gpx file',
            filetypes=[('Gps data file', '*.gpx'), ('All files', '*')])

        if gpx_file:  # user may close filedialog
            self.my_track.add_gpx(gpx_file.name)

            # Insert plot
            plots.plot_track(self.my_track, self.ax_track)
            plots.plot_elevation(self.my_track, self.ax_ele)
            track_info_table = plots.plot_track_info(self.my_track,
                                                     self.ax_track_info)
            plots.segment_selection(self.my_track, self.ax_track, self.ax_ele,
                                    self.fig_track, track_info_table)
            self.canvas.draw()

    def load_session(self):
        proceed = True

        if self.my_track.size > 0:
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
                    self.my_track.track = session_track
                    self.my_track.loaded_files = session_meta.loaded_files
                    self.my_track.size = session_meta.size
                    self.my_track.total_distance = session_meta.total_distance
                    self.my_track.extremes = session_meta.extremes

                    # Insert plot
                    plots.plot_track(self.my_track, self.ax_track)
                    plots.plot_elevation(self.my_track, self.ax_ele)
                    plots.plot_track_info(self.my_track, self.ax_track_info)
                    self.canvas.draw()

    def new_session(self):
        proceed = True

        if self.my_track.size > 0:
            message = \
                'Current session will be deleted. Do you wish to proceed?'
            proceed = messagebox.askokcancel(title='New session',
                                             message=message)

        if proceed:
            # Restart session
            self.my_track = track.Track()

            # Plot
            plots.plot_world(self.ax_track)
            plots.plot_no_elevation(self.ax_ele)
            plots.plot_no_info(self.ax_track_info)
            self.canvas.draw()

    def save_session(self):
        session = self.my_track.track

        metadata = types.SimpleNamespace()
        metadata.size = self.my_track.size
        metadata.extremes = self.my_track.extremes
        metadata.total_distance = self.my_track.total_distance
        metadata.loaded_files = self.my_track.loaded_files

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
        gpx_filename = tk.filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title='Save track as',
            filetypes=[('Gpx file', '*.gpx')])

        if gpx_filename:  # user may close filedialog
            self.my_track.save_gpx(gpx_filename)


if __name__ == '__main__':
    # Define logger
    if not os.path.isdir('log'):
        os.mkdir('log')

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime('%Y%m%d-%H%M%S')

    logging.basicConfig(level=c.log_level,
                        filename=f'log/{date_time}_track_editor.log')
    logger = logging.getLogger()

    # Initialize tk
    root = tk.Tk()
    root.wm_title('Track Editor')
    # root.geometry('800x800')
    MainApplication(root).pack(side='top', fill='both', expand=True)

    def quit_app():  # yes, it is redefined for windows
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.mainloop()
