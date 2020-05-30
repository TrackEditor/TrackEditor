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
