import logging
import datetime as dt
import os
import tkinter as tk
# import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as backend_tkagg
# import matplotlib.backend_bases as backend_bases  # key_press_handler
# import matplotlib.figure as figure  # import Figure
import numpy as np
import pandas as pd
import types

import track
import constants as c
import iosm
import utils


MY_TRACK = track.Track()

COLOR_LIST = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
              'blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'brown',
              'gold', 'turquoise', 'teal']


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


def plot_track(ob_track: track.Track, ax: plt.Figure.gca):
    ax.cla()

    map_img, bbox = generate_map(ob_track)

    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    segments_id = ob_track.track.segment.unique()
    for cc, seg_id in zip(COLOR_LIST, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.plot(segment.lon, segment.lat, color=cc,
                linewidth=1, marker='o', markersize=2, zorder=10)

    # Beauty salon
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def plot_elevation(ob_track: track.Track, ax: plt.Figure.gca):
    ax.cla()

    # Plot elevation
    segments_id = ob_track.track.segment.unique()

    for cc, seg_id in zip(COLOR_LIST, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
        ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

    ax.set_ylim((ob_track.track.ele.min() * 0.8,
                 ob_track.track.ele.max() * 1.2))

    # Set labels
    dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
    ele_label = [f'{int(item)} m' for item in ax.get_yticks()]

    if len(dist_label) != len(set(dist_label)):
        dist_label = [f'{item:.1f} km' for item in ax.get_xticks()]

    ax.set_xticklabels(dist_label)
    ax.set_yticklabels(ele_label)

    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=True)
    ax.tick_params(axis='y', left=False, right=False, labelleft=True)

    ax.grid(color='white')  # for some reason grid is removed from ggplot


def plot_world(ax: plt.Figure.gca):
    ax.clear()
    world_img = mpimg.imread(f'tiles/0/0/0.png')
    ax.imshow(world_img, zorder=0, aspect='equal')  # aspect is equal to ensure
    # square pixel
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def plot_no_elevation(ax: plt.Figure.gca):
    with plt.style.context('ggplot'):
        ax.plot()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
        ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def get_distance_label(ob_track: track.Track, segment_id: int = 1,
                       total: bool = False) -> str:
    if total:
        distance = ob_track.total_distance
    else:
        segment = ob_track.get_segment(segment_id)
        first = segment.iloc[0]
        last = segment.iloc[-1]

        if np.isnan(first['distance']):
            distance = last['distance']
        else:
            distance = last['distance'] - first['distance']

    if distance < 5:
        label = f'{distance:.2f} km'
    else:
        label = f'{distance:.1f} km'

    return label


def get_elevation_label(ob_track: track.Track, magnitude: str,
                        segment_id: int = 1, total: bool = False) -> str:
    if total:
        if 'pos' in magnitude:
            elevation = ob_track.total_uphill
        elif 'neg' in magnitude:
            elevation = ob_track.total_downhill
        else:
            elevation = 0
            print("[WARNING] Wrong input in function get_elevation_label")
    else:
        segment = ob_track.get_segment(segment_id)
        first = segment.iloc[0]
        last = segment.iloc[-1]

        if np.isnan(first[magnitude]):
            elevation = last[magnitude]
        else:
            elevation = last[magnitude] - first[magnitude]

    if abs(elevation) < 10:
        label = f'{elevation:.1f} m'
    else:
        label = f'{int(elevation)} m'

    if elevation > 0:
        label = f'+{label}'

    return label


def plot_track_info(ob_track: track.Track, ax: plt.Figure.gca):
    ax.cla()

    # Initialize table
    cell_text = []
    track_color = []

    # Build segments info table
    segments_id = ob_track.track.segment.unique()

    for cc, seg_id in zip(COLOR_LIST, segments_id):
        distance_lbl = get_distance_label(ob_track, segment_id=seg_id)
        gained_elevation_lbl = get_elevation_label(ob_track, 'ele_pos_cum',
                                                   segment_id=seg_id)
        lost_elevation_lbl = get_elevation_label(ob_track, 'ele_neg_cum',
                                                 segment_id=seg_id)

        cell_text.append(['',  # cell for color
                          distance_lbl,
                          gained_elevation_lbl,
                          lost_elevation_lbl])  # is negative

        track_color.append(cc)

    # Get info for the full track
    distance_lbl = get_distance_label(ob_track, -1, total=True)
    gained_elevation_lbl = get_elevation_label(ob_track, 'ele_pos_cum',
                                               total=True)
    lost_elevation_lbl = get_elevation_label(ob_track, 'ele_neg_cum',
                                             total=True)

    cell_text.append(['TOTAL',
                      distance_lbl,
                      gained_elevation_lbl,
                      lost_elevation_lbl])

    # Create table
    my_table = ax.table(cellText=cell_text,
                        loc='upper right',
                        edges='open',
                        colWidths=[1/6, 1/4, 1/4, 1/4])

    # Beauty salon
    my_table.set_fontsize(14)
    for row_idx, (row, row_cc) in enumerate(zip(cell_text, track_color)):
        my_table[row_idx, 0].visible_edges = 'BLRT'
        my_table[row_idx, 0].set_facecolor(row_cc)
        my_table[row_idx, 0].set_edgecolor('white')


def plot_no_info(ax: plt.Figure.gca):
    ax.cla()
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(False)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.fig = plt.figure(figsize=(8, 6), dpi=100)
        self.ax_ele = None
        self.ax_track = None
        self.ax_track_info = None
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
        # plot_empty(self.fig)
        gspec = gridspec.GridSpec(4, 8)

        # Plot world map
        plt.subplot(gspec[:3, :5])
        self.ax_track = plt.gca()
        plot_world(self.ax_track)

        # Plot fake elevation
        with plt.style.context('ggplot'):
            plt.subplot(gspec[3, :5])
            self.ax_ele = plt.gca()
            plot_no_elevation(self.ax_ele)

        # Text box
        plt.subplot(gspec[:3, 5:])
        self.ax_track_info = plt.gca()
        plot_no_info(self.ax_track_info)

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
            plot_track(self.my_track, self.ax_track)
            plot_elevation(self.my_track, self.ax_ele)
            plot_track_info(self.my_track, self.ax_track_info)
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
                    plot_track(self.my_track, self.ax_track)
                    plot_elevation(self.my_track, self.ax_ele)
                    plot_track_info(self.my_track, self.ax_track_info)
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
            plot_world(self.ax_track)
            plot_no_elevation(self.ax_ele)
            plot_no_info(self.ax_track_info)
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
