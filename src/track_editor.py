import logging
import datetime as dt
import os
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as backend_tkagg
import matplotlib.widgets as widgets
import types

import src.constants as c
import src.plots as plots
import src.track as track
from src.file_menu import FileMenu
from src.edit_menu import EditMenu
from src.utils import quit_app


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
        self.shared_data.my_track = track.Track()
        self.shared_data.cid = None

        # Initialize user interface
        self.init_ui()  # Insert default image

        # Create menu
        self.menubar = tk.Menu(self.parent)
        FileMenu(self.menubar, self)
        EditMenu(self.menubar, self)
        self.parent.config(menu=self.menubar)

        #  Insert navigation toolbar for plots
        toolbar = backend_tkagg.NavigationToolbar2Tk(self.shared_data.canvas,
                                                     root)
        toolbar.children['!button3'].pack_forget()  # forward to next view
        toolbar.children['!button5'].pack_forget()  # zoom to rectangle
        toolbar.children['!button6'].pack_forget()  # configure subplots
        toolbar.children['!button7'].pack_forget()  # save figure
        toolbar.update()
        self.shared_data.canvas.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH, expand=1)

    def init_ui(self):
        # Prepare plot grid distribution
        gspec = gridspec.GridSpec(4, 8)

        # Plot world map
        plt.subplot(gspec[:3, :5])
        self.shared_data.ax_track = plt.gca()
        self.shared_data.fig_track = plt.gcf()
        plots.plot_world(self.shared_data.ax_track)

        # Plot fake elevation
        with plt.style.context('ggplot'):
            plt.subplot(gspec[3, :5])
            self.shared_data.ax_ele = plt.gca()
            self.shared_data.fig_ele = plt.gcf()
            plots.plot_no_elevation(self.shared_data.ax_ele)

        # Text box
        plt.subplot(gspec[:3, 5:])
        self.shared_data.ax_track_info = plt.gca()
        self.shared_data.fig_track_info = plt.gcf()
        plots.plot_no_info(self.shared_data.ax_track_info)

        # Button
        button_position = plt.axes([0.8, 0.025, 0.1, 0.04])
        self.shared_data.btn_done = widgets.Button(button_position, '$Done$')
        self.shared_data.btn_done.hovercolor = self.shared_data.btn_done.color
        self.shared_data.btn_done.label._color = '0.6'

        self.shared_data.canvas.get_tk_widget().pack(expand=True, fill='both')


if __name__ == '__main__':
    # Define logger
    if not os.path.isdir('log'):
        os.mkdir('../log')

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime('%Y%m%d-%H%M%S')

    logging.basicConfig(level=c.log_level,
                        filename=f'log/{date_time}_track_editor.log')
    logger = logging.getLogger()

    # Initialize tk
    root = tk.Tk()
    root.wm_title('Track Editor')
    # root.geometry('1200x800')
    MainApplication(root).pack(side='top', fill='both', expand=True)

    root.protocol("WM_DELETE_WINDOW", lambda: quit_app(root))
    root.mainloop()
