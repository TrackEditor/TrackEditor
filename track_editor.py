import logging
import datetime as dt
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as  backend_tkagg  # import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.backend_bases as backend_bases  # key_press_handler
import matplotlib.figure as figure  # import Figure
import numpy as np
import pandas as pd

import gpx
import track
import constants as c
import iosm
import utils


MY_TRACK = track.Track()


def create_map_img(extreme_tiles: tuple, zoom: int) -> np.array:
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f"tiles/{zoom}/{x}/{ytile}.png")

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f"tiles/{zoom}/{x}/{y}.png"
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

    # Download missing tiles
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max, max_zoom=zoom)

    # Generate map image
    extreme_tiles = get_extreme_tiles(ob_track, zoom)
    map_img = create_map_img(extreme_tiles, zoom)

    # Define map box
    bbox = get_map_box(extreme_tiles, zoom)

    return map_img, bbox


def plot_gpx(ob_track: track.Track):
    color_list = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
                  'blue', 'green', 'red', 'cyan', 'magenta', 'yellow'
                  'brown', 'gold', 'turquoise', 'teal']

    map_img, bbox = generate_map(ob_track)

    # Plots
    plt.figure()
    gspec = gridspec.GridSpec(4, 1)

    # Plot map
    plt.subplot(gspec[:3, 0])
    ax = plt.gca()
    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    segments_id = ob_track.track.segment.unique()
    for c, seg_id in zip(color_list, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.plot(segment.lon, segment.lat, color=c,
                linewidth=1, marker='o', markersize=2)

    # Beauty salon
    plt.tick_params(axis="x", bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis="y", left=False, right=False, labelleft=False)

    # Plot elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        ax = plt.gca()
        for c, seg_id in zip(color_list, segments_id):
            segment = ob_track.get_segment(seg_id)
            ax.fill_between(segment.distance, segment.ele, alpha=0.2)
            ax.plot(segment.distance, segment.ele, linewidth=2)

        ax.set_ylim((ob_track.track.ele.min() * 0.8,
                     ob_track.track.ele.max() * 1.2))

        # TODO tuning for low distances labeling
        dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
        ele_label = [f'{int(item)} m' for item in ax.get_yticks()]
        ax.set_xticklabels(dist_label)
        ax.set_yticklabels(ele_label)

    return plt.gcf()


def quit_app():
    root.quit()  # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


def load_track():
    gpx_file = tk.filedialog.askopenfile(initialdir=os.getcwd(),
                                              title="Select gpx file",
                                              filetypes=[
                                                  ("Gps data file", "*.gpx")])
    # Load gpx file
    MY_TRACK.add_gpx(gpx_file.name)

    # Insert plot
    fig = plot_gpx(MY_TRACK)
    canvas = backend_tkagg.FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


class Application(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent


if __name__ == "__main__":
    # Define logger
    if not os.path.isdir("log"):
        os.mkdir("log")

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime("%Y%m%d-%H%M%S")

    logging.basicConfig(level=c.log_level,
                        filename=f"log/{date_time}_track_editor.log")
    logger = logging.getLogger()

    # Initialize tk
    root = tk.Tk()
    root.wm_title("Embedding in Tk")

    # Menu
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Load track", command=load_track)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=quit_app)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)

    # TODO:re-restructure https://stackoverflow.com/questions/17466561/best-way-to-structure-a-tk-application

    tk.mainloop()
