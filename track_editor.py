import logging
import datetime as dt
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as backend_tkagg
import matplotlib.backend_bases as backend_bases  # key_press_handler
import matplotlib.figure as figure  # import Figure
import numpy as np
import pandas as pd
import types

import track
import constants as c
import iosm
import utils


MY_TRACK = track.Track()


def create_map_img(extreme_tiles: tuple, zoom: int) -> np.array:
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f'tiles/{zoom}/{x}/{ytile}.png')

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f'tiles/{zoom}/{x}/{y}.png'
            local_img = mpimg.imread(local_img_path)
            y_img = np.vstack((y_img, local_img))

        if map_img is not None:
            map_img = np.hstack((map_img, y_img))
        else:
            map_img = y_img

    return map_img


# def optimize_aspect_ratio(extreme_tiles):
#     xtile, ytile, final_xtile, final_ytile = extreme_tiles
#
#     # Initialize error
#     ar = get_aspect_ratio(xtile, ytile, final_xtile, final_ytile)
#     error_cur = abs(c.aspect_ratio - ar)
#     error_prev = error_cur + 1
#
#     # Optimize final aspect ratio
#     while error_prev > error_cur:
#
#         if ar < c.aspect_ratio:
#             final_xtile += 1  # TODO: increase or decrease xtile and final_xtile alternatively
#         elif ar > c.aspect_ratio:
#             final_ytile += 1
#
#         # Update error
#         ar = get_aspect_ratio(xtile, ytile, final_xtile, final_ytile)
#         error_prev = error_cur
#         error_cur = abs(c.aspect_ratio - ar)
#
#     return xtile, ytile, final_xtile, final_ytile
#
#
# def get_aspect_ratio(xtile: int, ytile: int, final_xtile: int,
#                      final_ytile: int) -> float:
#     width = final_xtile - xtile
#     height = final_ytile - ytile
#
#     if width < 0 or height < 0:
#         print(
#             f'[ERROR] Negative proportion: width={width}, height={height}')
#
#     return width/height


def get_extreme_tiles(ob_track: track.Track, zoom: int):
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    xtile, ytile = iosm.deg2num(lat_max, lon_min, zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, zoom)

    return xtile, ytile, final_xtile, final_ytile


def get_map_box(extreme_tiles, zoom):
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    ymax, xmax = iosm.num2deg(final_xtile + 1, ytile, zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile + 1, zoom)
    bbox = (xmin, xmax, ymin, ymax)
    return bbox


def generate_map(ob_track: track.Track) -> np.array:
    # Define map perspective
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    zoom = utils.auto_zoom(lat_min, lon_min, lat_max, lon_max)

    extreme_tiles = get_extreme_tiles(ob_track, zoom)
    extreme_tiles_expanded = (extreme_tiles[0] - c.margin_outbounds,  # x
                              extreme_tiles[1] - c.margin_outbounds,  # y
                              extreme_tiles[2] + c.margin_outbounds,  # xfinal
                              extreme_tiles[3] + c.margin_outbounds)  # yfinal

    # Download missing tiles
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max,
                        max_zoom=zoom, extra_tiles=c.margin_outbounds)

    # Generate map image
    map_img = create_map_img(extreme_tiles_expanded, zoom)

    # Define map box
    bbox = get_map_box(extreme_tiles_expanded, zoom)

    return map_img, bbox


def plot_gpx(ob_track: track.Track, fig: plt.figure):
    """
    Plot tracks from all gpx loaded files in the provided figure. Uses Open
    Street Map as background.
    :param ob_track: track class object where coordinates data frame are stored
    :param fig: matplotlib figures from user interface
    """
    color_list = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
                  'blue', 'green', 'red', 'cyan', 'magenta', 'yellow'
                  'brown', 'gold', 'turquoise', 'teal']

    map_img, bbox = generate_map(ob_track)

    # Plots
    gspec = gridspec.GridSpec(4, 1)

    # Plot map
    plt.subplot(gspec[:3, 0])
    ax = plt.gca()
    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    segments_id = ob_track.track.segment.unique()
    for cc, seg_id in zip(color_list, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.plot(segment.lon, segment.lat, color=cc,
                linewidth=1, marker='o', markersize=2, zorder=10)

    # Beauty salon
    plt.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis='y', left=False, right=False, labelleft=False)

    # Plot elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        ax = plt.gca()
        for cc, seg_id in zip(color_list, segments_id):
            segment = ob_track.get_segment(seg_id)
            ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
            ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

        ax.set_ylim((ob_track.track.ele.min() * 0.8,
                     ob_track.track.ele.max() * 1.2))

        # TODO tuning for low distances labeling
        dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
        ele_label = [f'{int(item)} m' for item in ax.get_yticks()]
        ax.set_xticklabels(dist_label)
        ax.set_yticklabels(ele_label)


def plot_empty(ob_track: track.Track, fig: plt.figure):
    color_list = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
                  'blue', 'green', 'red', 'cyan', 'magenta', 'yellow'
                  'brown', 'gold', 'turquoise', 'teal']

    # Plots
    gspec = gridspec.GridSpec(4, 1)

    # Plot map
    plt.subplot(gspec[:3, 0])
    ax = plt.gca()

    world_img = mpimg.imread(f'tiles/0/0/0.png')
    ax.imshow(world_img, zorder=0, aspect='equal')  # aspect is equal to


    # Plot track
    segments_id = ob_track.track.segment.unique()
    for cc, seg_id in zip(color_list, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.plot(segment.lon, segment.lat, color=cc,
                linewidth=1, marker='o', markersize=2, zorder=10)

    # Beauty salon
    plt.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis='y', left=False, right=False, labelleft=False)

    # Plot elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        ax = plt.gca()
        for cc, seg_id in zip(color_list, segments_id):
            segment = ob_track.get_segment(seg_id)
            ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
            ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

        # ax.set_ylim((ob_track.track.ele.min() * 0.8,
        #              ob_track.track.ele.max() * 1.2))

        # TODO tuning for low distances labeling
        # dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
        # ele_label = [f'{int(item)} m' for item in ax.get_yticks()]
        # ax.set_xticklabels(dist_label)
        # ax.set_yticklabels(ele_label)


def plot_empty2(fig: plt.figure):
    allaxes = fig.get_axes()
    print(allaxes)
    print(len(allaxes))
    
    gspec = gridspec.GridSpec(4, 1)

    # Plot world map
    plt.subplot(gspec[:3, 0])
    plt.gca().clear()

    world_img = mpimg.imread(f'tiles/0/0/0.png')
    plt.imshow(world_img, zorder=0, aspect='equal')  # aspect is equal to
    # ensure square pixel
    plt.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis='y', left=False, right=False, labelleft=False)

    # Plot fake elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        plt.gca().clear()
        plt.plot()


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.fig = plt.figure(figsize=(8, 6), dpi=100)
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
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit', command=self.quit_app)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.parent.config(menu=self.menubar)

        #  Insert navigation toolbar for plots
        toolbar = backend_tkagg.NavigationToolbar2Tk(self.canvas, root)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def init_ui(self):
        plot_empty(self.my_track, self.fig)
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
            plot_gpx(self.my_track, self.fig)
            self.canvas.draw()

    def load_session(self):
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
                plot_gpx(self.my_track, self.fig)
                self.canvas.draw()

    def new_session(self):
        print("New session")
        self.fig.clf()
        self.my_track = track.Track()
        plot_empty(self.my_track, self.fig)
        print("New session plot?")

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
    root.mainloop()
