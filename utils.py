import hashlib

import constants as c
import iosm


def auto_zoom(lat_min: float, lon_min: float,
              lat_max: float, lon_max: float) -> int:
    """
    Compute the best zoom to show a complete track. It must contain the full
    track in more than one tail but minimising the number of tails.
    :param lat_min: furthest south point
    :param lon_min: furthest west point
    :param lat_max: furthest north point
    :param lon_max: furthest east point
    :return: zoom to use to show full track
    """

    for zoom in range(c.max_zoom):
        num_x_min, num_y_min = iosm.deg2num(lat_min, lon_min, zoom)
        num_x_max, num_y_max = iosm.deg2num(lat_max, lon_max, zoom)

        number_tiles = abs((num_x_max - num_x_min) * (num_y_max - num_y_min))

        if number_tiles > 1:
            return zoom

    return c.max_zoom


def md5sum(file: str) -> str:
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
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                            (float(iteration) / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length - 1)

    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='')
