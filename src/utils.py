"""UTILS
General purpose functions

Author: alguerre
License: MIT
"""
import hashlib
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import types
from typing import Tuple
import threading
import queue

import numpy as np
import matplotlib.colors as mcolors


def md5sum(file: str) -> str:
    """
    Create a strings with the md5 of a given file
    :param file: filename of the file whose md5 is computed for
    :return: md5 string
    """
    md5_hash = hashlib.md5()

    a_file = open(file, "rb")
    content = a_file.read()
    md5_hash.update(content)

    digest = md5_hash.hexdigest()

    return digest


def print_progress_bar(iteration: int, total: int,
                       prefix: str = '', suffix: str = '', decimals: int = 1,
                       length: int = 100, fill: str = '|'):
    """
    Call in a loop to create terminal progress bar
    :param iteration: current iteration
    :param total: total iterations
    :param prefix: prefix string
    :param suffix: suffix string
    :param decimals: positive number of decimals in percent complete
    :param length: character length of bar
    :param fill: bar fill character
    """
    percent = \
        ("{0:." + str(decimals) + "f}").format(
            100 * (float(iteration) / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length - 1)

    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='')


def not_implemented(function: types.FunctionType):
    """
    Decorator to show warning for not implemented functionalities
    :param function: not implemented function
    :return: wrapper function
    """
    def wrapper_function(*args, **kwargs):
        messagebox.showwarning(
            'Warning',
            f'Not implemented functionality: {function.__name__}')
    return wrapper_function


def exception_handler(function: types.FunctionType):
    """
    Decorator to show warning for not implemented functionalities
    :param function: not implemented function
    :return: wra
    """
    def wrapper_function(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception as e:
            messagebox.showerror(
                'Error',
                f'Exception at {function.__name__}\n{e}')
    return wrapper_function


def moving_average(a, n: int = 3):
    """
    Naive moving average implementation
    :param a: numpy array
    :param n: point mean values
    :return: smooth numpy array
    """
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


def quit_app(parent: tk.Tk):
    """
    Quit the app safely when using exit option or cross symbol.
    :param parent: tkinter window of the main app
    """
    parent.quit()  # stops mainloop
    parent.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


def color_rgb(color_name: str) -> Tuple[float, float, float]:
    color_collection = mcolors.CSS4_COLORS

    by_hsv = sorted((tuple(mcolors.to_rgb(color)), name)
                    for name, color in color_collection.items())

    for color in by_hsv:
        if color_name == color[1]:
            return color[0]

    return 0.0, 0.0, 0.0


def rgb2hexcolor(rgb_color: Tuple[float, float, float]) -> str:
    return '#%02x%02x%02x' % (int(255*rgb_color[0]),
                              int(255*rgb_color[1]),
                              int(255*rgb_color[2]))


class Progress:
    def __init__(self, parent):
            self.toplevel = tk.Toplevel(parent)
            self.progressbar = ttk.Progressbar(self.toplevel,
                                               orient=tk.HORIZONTAL,
                                               mode='indeterminate')
            self.progressbar.pack()
            self.t = threading.Thread()
            self.t.__init__(target=self.progressbar.start, args=(5,))
            self.t.start()

    def end(self):
        if not self.t.is_alive():
            self.progressbar.stop()
            self.toplevel.destroy()
            self.t.join()


def manage_queue(q, func, args):
    func(*args)
    q.put('finish')


def execute_with_progressbar(master, func, *args):
    q = queue.Queue()
    q.put('init')

    threading.Thread(target=manage_queue, args=(q, func, args)).start()
    p = Progress(master)

    def wait_thread():
        if not q.empty():
            element = q.get(0)
            if element == 'finish':
                p.end()
                return True
            else:
                master.after(100, wait_thread)
        else:
            master.after(100, wait_thread)

    wait_thread()
