import logging
from typing import Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopy.distance
from matplotlib.font_manager import FontProperties
import matplotlib.ticker as mticker

import iosm
import track
import map_generator as mg


CLICK_DISTANCE = 0.25  # default value

logger = logging.getLogger(__name__)


COLOR_LIST = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
              'blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'brown',
              'gold', 'turquoise', 'teal']

N_COLOR = len(COLOR_LIST)


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
            logger.warning('Wrong input in function get_elevation_label')
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
    segments_id = ob_track.df_track.segment.unique()

    for seg_id in segments_id:
        distance_lbl = get_distance_label(ob_track, segment_id=seg_id)
        gained_elevation_lbl = get_elevation_label(ob_track, 'ele_pos_cum',
                                                   segment_id=seg_id)
        lost_elevation_lbl = get_elevation_label(ob_track, 'ele_neg_cum',
                                                 segment_id=seg_id)

        cell_text.append([seg_id,  # cell for color
                          distance_lbl,
                          gained_elevation_lbl,
                          lost_elevation_lbl])

        track_color.append(COLOR_LIST[(seg_id-1) % N_COLOR])

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
        my_table[row_idx, 0].get_text().set_color(row_cc)  # this text will be
        # kind of invisible
        my_table[row_idx, 0].set_edgecolor('white')

    return my_table  # this allows table modifications after plot


def plot_no_info(ax: plt.Figure.gca):
    ax.cla()
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_track(ob_track: track.Track, ax: plt.Figure.gca):
    global CLICK_DISTANCE
    ax.cla()

    # Plot map
    map_img, bbox = mg.generate_map(ob_track)
    CLICK_DISTANCE = mg.get_click_distance(bbox)
    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    segments_id = ob_track.df_track.segment.unique()
    for seg_id in segments_id:
        cc = COLOR_LIST[(seg_id - 1) % N_COLOR]  # color
        segment = ob_track.get_segment(seg_id)
        reduced_segment = mg.point_reduction(segment)
        ax.plot(reduced_segment.lon, reduced_segment.lat, color=cc,
                linewidth=1, marker='o', markersize=2, zorder=10)

    # Join tracks
    for i in range(len(segments_id)-1):
        # Line from last point in current segment to last in next segment
        curr_segment = ob_track.get_segment(segments_id[i])
        next_segment = ob_track.get_segment(segments_id[i+1])
        ax.plot([curr_segment.iloc[-1].lon, next_segment.iloc[0].lon],
                [curr_segment.iloc[-1].lat, next_segment.iloc[0].lat],
                color='red', linewidth=1, zorder=9)

    # Beauty salon
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def get_closest_segment(df_track: pd.DataFrame, point: Tuple[float, float]):
    df_track['point_distance'] = df_track.apply(
        lambda row: geopy.distance.geodesic((row.lat, row.lon), point).km,
        axis=1)
    min_row = \
        df_track[df_track.point_distance == df_track.point_distance.min()]
    min_distance = min_row.point_distance.iloc[0]
    min_segment = min_row.segment.iloc[0]
    df_track.drop('point_distance', axis=1, inplace=True)

    return min_distance, int(min_segment)


def _deselect_segment(ob_track: track.Track):
    if ob_track.selected_segment:
        for selected_track in ob_track.selected_segment:
            selected_track.remove()
        ob_track.selected_segment = []
        ob_track.selected_segment_idx = []


def _select_segment(seg2select: int, ob_track: track.Track,
                    ax_track: plt.Figure.gca):
    segment = ob_track.get_segment(seg2select)
    selected_segment, = ax_track.plot(segment.lon, segment.lat,
                                      color=COLOR_LIST[(seg2select - 1)
                                                       % N_COLOR],
                                      linewidth=4,
                                      zorder=10)
    ob_track.selected_segment.append(selected_segment)
    ob_track.selected_segment_idx.append(seg2select)


def _select_track_info(track_info_table, seg2select: int = 0,
                       deselect: bool = False):
    table_size = sorted(track_info_table.get_celld().keys())[-1]
    max_idx_row = table_size[0]
    max_idx_col = table_size[1]

    for i_row in range(max_idx_row + 1):
        head_cell = track_info_table[i_row, 0]
        segment_txt = head_cell.get_text()._text
        if segment_txt.isnumeric():
            if int(segment_txt) == seg2select and not deselect:
                for i_col in range(max_idx_col + 1):
                    cell = track_info_table[i_row, i_col]
                    cell.set_text_props(
                        fontproperties=FontProperties(weight='bold'))
            else:
                for i_col in range(max_idx_col + 1):
                    cell = track_info_table[i_row, i_col]
                    cell.set_text_props(
                        fontproperties=FontProperties())


def segment_selection(ob_track: track.Track, ax_track: plt.Figure.gca,
                      ax_elevation: plt.Figure.gca, fig_track: plt.Figure,
                      track_info_table):

    def on_click(event):

        # Check click limits before operation
        xlim = ax_track.get_xlim()
        ylim = ax_track.get_ylim()
        try:
            if event.xdata < min(xlim) or event.xdata > max(xlim) or \
                    event.ydata < min(ylim) or event.ydata > max(ylim):
                return
        except TypeError:
            return

        # Click position to distance
        if event.xdata and event.ydata:
            point_distance, seg2select = \
                get_closest_segment(ob_track.df_track,
                                    (event.ydata, event.xdata))
        else:  # click outside plot
            point_distance = 1e+10
            seg2select = 0

        # Highlight track and elevation
        if point_distance < CLICK_DISTANCE and seg2select > 0:
            _deselect_segment(ob_track)  # deselect current segment if needed
            _select_segment(seg2select, ob_track, ax_track)

            plot_elevation(ob_track, ax_elevation,
                           selected_segment_idx=seg2select)
            _select_track_info(track_info_table, seg2select=seg2select)
        else:
            _deselect_segment(ob_track)
            plot_elevation(ob_track, ax_elevation)
            _select_track_info(track_info_table, deselect=True)

        fig_track.canvas.draw()

    cid = fig_track.canvas.mpl_connect('button_press_event', on_click)
    return cid


def plot_elevation(ob_track: track.Track, ax: plt.Figure.gca,
                   selected_segment_idx: int = 0):
    ax.cla()

    # Plot elevation
    segments_id = ob_track.df_track.segment.unique()

    if selected_segment_idx == 0:
        for seg_id in segments_id:
            cc = COLOR_LIST[(seg_id-1) % N_COLOR]  # color
            segment = ob_track.get_segment(seg_id)
            ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
            ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

        for i in range(len(segments_id)-1):
            curr_segment = ob_track.get_segment(segments_id[i])
            next_segment = ob_track.get_segment(segments_id[i+1])
            ax.plot([curr_segment.distance.iloc[-1],
                     next_segment.distance.iloc[0]],
                    [curr_segment.ele.iloc[-1], next_segment.ele.iloc[0]],
                    linewidth=2, color='red', linestyle='-.')
            ax.fill_between([curr_segment.distance.iloc[-1],
                             next_segment.distance.iloc[0]],
                            [curr_segment.ele.iloc[-1],
                             next_segment.ele.iloc[0]],
                            alpha=0.5, color='red')
    else:
        segment = ob_track.get_segment(selected_segment_idx)
        cc = COLOR_LIST[(selected_segment_idx - 1) % N_COLOR]
        ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
        ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

    ax.set_ylim((ob_track.df_track.ele.min() * 0.8,
                 ob_track.df_track.ele.max() * 1.2))

    # Set labels
    dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
    ele_label = [f'{int(item)} m' for item in ax.get_yticks()]

    if len(dist_label) != len(set(dist_label)):
        dist_label = [f'{item:.1f} km' for item in ax.get_xticks()]

    ax.xaxis.set_major_locator(mticker.FixedLocator(ax.get_xticks()))
    ax.yaxis.set_major_locator(mticker.FixedLocator(ax.get_yticks()))
    # locators are need to avoid warning

    ax.set_xticklabels(dist_label)
    ax.set_yticklabels(ele_label)

    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=True)
    ax.tick_params(axis='y', left=False, right=False, labelleft=True)

    ax.grid(color='white')  # for some reason grid is removed from ggplot


def plot_world(ax: plt.Figure.gca):
    iosm.download_tiles_by_num(0, 0, 1, 1, max_zoom=1)

    ax.clear()
    world_img = mg.create_map_img((0, 0, 1, 1), 1)
    ax.imshow(world_img, zorder=0, aspect='equal')  # aspect is equal to ensure
    # square pixel
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def plot_no_elevation(ax: plt.Figure.gca):
    with plt.style.context('ggplot'):
        ax.cla()
        ax.plot()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
        ax.tick_params(axis='y', left=False, right=False, labelleft=False)
