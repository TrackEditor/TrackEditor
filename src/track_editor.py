"""TRACK_EDITOR
This is a graphical tool to edit GPX files in a graphical environment.
Overview:
    - File menu: functionalities to load and save your files
    - Edit menu: options to edit the loaded tracks
    - Panel: track and elevation plots, segments information box

This module includes the main function of the tool and defines the global
GUI aspect.

Author: alguerre
License: MIT
"""
import logging
import datetime as dt
import os
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as backend_tkagg
import matplotlib.widgets as widgets
import types

import constants as c
import plots
import track
from file_menu import FileMenu
from edit_menu import EditMenu
from utils import quit_app


class MainApplication(tk.Frame):
    """
    Manage the control of data and behaviour of the overall user interface.
    Defines shared data: figures, axes and track object, define figure and
    menus.
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.fig = plt.figure(figsize=(12, 8), dpi=100)

        # Define shared data
        self.shared_data = types.SimpleNamespace()
        self.shared_data.ax_ele = None
        self.shared_data.ax_track = None
        self.shared_data.ax_track_info = None
        self.shared_data.fig_ele = None
        self.shared_data.fig_track = None
        self.shared_data.fig_track_info = None
        self.shared_data.canvas = backend_tkagg.FigureCanvasTkAgg(self.fig,
                                                                  self)
        self.shared_data.obj_track = track.Track()
        self.shared_data.cid = []

        # Initialize user interface
        self.init_ui()  # Insert default image

        # Create menu
        self.menubar = tk.Menu(self.parent)
        FileMenu(self.menubar, self)
        EditMenu(self.menubar, self)
        self.parent.config(menu=self.menubar)

    def init_ui(self):
        # Prepare plot grid distribution
        gspec = gridspec.GridSpec(4, 8)

        # World map - define subplot space
        plt.subplot(gspec[:3, :5])
        self.shared_data.ax_track = plt.gca()
        self.shared_data.fig_track = plt.gcf()

        # Elevation - define subplot space
        with plt.style.context('ggplot'):
            plt.subplot(gspec[3, :5])
            self.shared_data.ax_ele = plt.gca()
            self.shared_data.fig_ele = plt.gcf()

        # Text box - define subplot space
        plt.subplot(gspec[:3, 5:])
        self.shared_data.ax_track_info = plt.gca()
        self.shared_data.fig_track_info = plt.gcf()

        # Insert plots
        plots.initial_plots(
            self.shared_data.ax_track,
            self.shared_data.ax_ele,
            self.shared_data.ax_track_info)

        # Button
        button_position = plt.axes([0.8, 0.025, 0.1, 0.04])
        self.shared_data.btn_done = widgets.Button(button_position, '$Done$')
        self.shared_data.btn_done.hovercolor = self.shared_data.btn_done.color
        self.shared_data.btn_done.label._color = '0.6'

        self.shared_data.canvas.get_tk_widget().pack(expand=True, fill='both')


if __name__ == '__main__':
    # Define logger
    if not os.path.isdir(f'{c.prj_path}/log'):
        os.mkdir(f'{c.prj_path}/log')

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime('%Y%m%d-%H%M%S')

    logging.basicConfig(
        level=c.log_level,
        filename=f'{c.prj_path}/log/{date_time}_track_editor.log')
    logger = logging.getLogger()

    # Initialize tk
    root = tk.Tk()
    root.wm_title('Track Editor')
    # root.geometry('1200x800')
    MainApplication(root).pack(side='top', fill='both', expand=True)

    root.protocol("WM_DELETE_WINDOW", lambda: quit_app(root))
    root.mainloop()
