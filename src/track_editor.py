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

from src import constants as c, utils, plots, track

# import iosm


MY_TRACK = track.Track()


class MainApplication(tk.Frame):
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

        # Initialize user interface
        self.init_ui()  # Insert default image

        # Create menu
        self.menubar = tk.Menu(self.parent)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.define_filemenu()
        self.define_editmenu()

        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.menubar.add_cascade(label='Edit', menu=self.editmenu)
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

        self.shared_data.canvas.get_tk_widget().pack(expand=True, fill='both')

    def define_filemenu(self):
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

    def define_editmenu(self):
        self.editmenu.add_command(label='Cut', command=utils.not_implemented)
        self.editmenu.add_command(label='Reverse',
                                  command=utils.not_implemented)
        self.editmenu.add_command(label='Insert time',
                                  command=utils.not_implemented)
        self.editmenu.add_command(label='Correct elevation',
                                  command=utils.not_implemented)
        self.editmenu.add_command(label='Split segment',
                                  command=utils.not_implemented)

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
            self.shared_data.my_track.add_gpx(gpx_file.name)

            # Insert plot
            plots.plot_track(self.shared_data.my_track,
                             self.shared_data.ax_track)
            plots.plot_elevation(self.shared_data.my_track,
                                 self.shared_data.ax_ele)
            track_info_table = plots.plot_track_info(
                self.shared_data.my_track, self.shared_data.ax_track_info)
            plots.segment_selection(self.shared_data.my_track,
                                    self.shared_data.ax_track,
                                    self.shared_data.ax_ele,
                                    self.shared_data.fig_track,
                                    track_info_table)
            self.shared_data.canvas.draw()

    def load_session(self):
        proceed = True

        if self.shared_data.my_track.size > 0:
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
                    self.shared_data.my_track.track = session_track
                    self.shared_data.my_track.loaded_files = \
                        session_meta.loaded_files
                    self.shared_data.my_track.size = session_meta.size
                    self.shared_data.my_track.total_distance = \
                        session_meta.total_distance
                    self.shared_data.my_track.extremes = session_meta.extremes

                    # Insert plot
                    plots.plot_track(self.shared_data.my_track,
                                     self.shared_data.ax_track)
                    plots.plot_elevation(self.shared_data.my_track,
                                         self.shared_data.ax_ele)
                    plots.plot_track_info(self.shared_data.my_track,
                                          self.shared_data.ax_track_info)
                    self.shared_data.canvas.draw()

    def new_session(self):
        proceed = True

        if self.shared_data.my_track.size > 0:
            message = \
                'Current session will be deleted. Do you wish to proceed?'
            proceed = messagebox.askokcancel(title='New session',
                                             message=message)

        if proceed:
            # Restart session
            self.shared_data.my_track = track.Track()

            # Plot
            plots.plot_world(self.shared_data.ax_track)
            plots.plot_no_elevation(self.shared_data.ax_ele)
            plots.plot_no_info(self.shared_data.ax_track_info)
            self.shared_data.canvas.draw()

    def save_session(self):
        session = self.shared_data.my_track.track

        metadata = types.SimpleNamespace()
        metadata.size = self.shared_data.my_track.size
        metadata.extremes = self.shared_data.my_track.extremes
        metadata.total_distance = self.shared_data.my_track.total_distance
        metadata.loaded_files = self.shared_data.my_track.loaded_files

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
            self.shared_data.my_track.save_gpx(gpx_filename)


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

    def quit_app():  # yes, it is redefined for windows
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.mainloop()