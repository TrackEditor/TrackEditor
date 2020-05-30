import logging
import datetime as dt
import os
import tkinter
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.backends.backend_tkagg as  backend_tkagg  #import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.backend_bases as backend_bases  #key_press_handler
import matplotlib.figure as figure  #import Figure
import numpy as np
import pandas as pd


import gpx
import constants as c
import iosm
import utils


def plot_gpx(df_track: pd.DataFrame):
    # Get extremes values
    lat_min = df_track["lat"].min()
    lat_max = df_track["lat"].max()
    lon_min = df_track["lon"].min()
    lon_max = df_track["lon"].max()

    # Select optimal zoom
    zoom = utils.auto_zoom(lat_min, lon_min, lat_max, lon_max)

    # Download OSM tiles if needed
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max)

    # Get map image
    xtile, ytile = iosm.deg2num(lat_max, lon_min, zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, zoom)

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

    # Plots
    plt.figure()
    gspec = gridspec.GridSpec(4, 1)

    # Plot map
    plt.subplot(gspec[:3, 0])
    ax = plt.gca()
    ymax, xmax = iosm.num2deg(final_xtile+1, ytile, zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile+1, zoom)
    bbox = (xmin, xmax, ymin, ymax)
    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    ax.scatter(df_track.lon, df_track.lat, s=5)

    # Beauty salon
    plt.tick_params(axis="x", bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis="y", left=False, right=False, labelleft=False)

    ax.set_xlim((xmin, xmax))
    ax.set_ylim((ymin, ymax))

    # Plot elevation
    with plt.style.context('ggplot'):
        plt.subplot(gspec[3, 0])
        ax = plt.gca()
        ax.fill_between(np.arange(len(df_track)), df_track.ele)
        ax.set_ylim((df_track.ele.min()*0.8, df_track.ele.max()*1.2))

    return plt.gcf()  # plt.show()


def quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


def donothing():
    print("donothing")


def load_track():
    gpx_file = tkinter.filedialog.askopenfile(initialdir=os.getcwd(),
                                              title="Select gpx file",
                                              filetypes=[("Gps data file", "*.gpx")])
    # Load gpx file
    gpx_track = gpx.Gpx(gpx_file.name)
    df_gpx = gpx_track.to_pandas()

    # Insert plot
    fig = plot_gpx(df_gpx)
    canvas = backend_tkagg.FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


if __name__ == "__main__":
    # Define logger
    if not os.path.isdir("log"):
        os.mkdir("log")

    now = dt.datetime.now()  # current date and time
    date_time = now.strftime("%Y%m%d-%H%M%S")

    logging.basicConfig(level=c.log_level,
                        filename=f"log/{date_time}_track_editor.log")
    logger = logging.getLogger()

    # # Load gpx file
    # my_route = "test_cases/nominal_route.gpx"
    # gpx_track = gpx.Gpx(my_route)
    # df_gpx = gpx_track.to_pandas()
    
    # Initialize tkinter
    root = tkinter.Tk()
    root.wm_title("Embedding in Tk")

    # # Insert plot
    # fig = plot_gpx(df_gpx)
    # canvas = backend_tkagg.FigureCanvasTkAgg(fig, master=root)
    # canvas.draw()
    # canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    # Menu
    menubar = tkinter.Menu(root)
    filemenu = tkinter.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Load track", command=load_track)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)

    tkinter.mainloop()
