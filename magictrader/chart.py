import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import mpl_finance as mpf
from matplotlib import colors as mcolors
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from six.moves import xrange, zip

from magictrader.candle import Candle
from magictrader.indicator import Indicator


class ChartWindow:
    """
    チャートに表示するウインドウを表すクラス
    """

    def __init__(self):

        self._title = ""
        self._xlabel = ""
        self._ylabel_left = ""
        self._ylabel_right = ""
        self._legend_visible = True
        self._grid = False
        self._height_ratio = 1
        self._candle = None
        self._indicators_left = []
        self._indicators_right = []
        self._plt_axes_left = None
        self._plt_axes_right = None
        self._plt_candle_handler = None
        self._plt_indicator_left_handlers = []
        self._plt_indicator_right_handlers = []

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value

    @property
    def xlabel(self) -> str:
        return self._xlabel

    @xlabel.setter
    def xlabel(self, value: str):
        self._xlabel = value

    @property
    def ylabel_left(self) -> str:
        return self._ylabel_left

    @ylabel_left.setter
    def ylabel_left(self, value: str):
        self._ylabel_left = value

    @property
    def ylabel_right(self) -> str:
        return self._ylabel_right

    @ylabel_right.setter
    def ylabel_right(self, value: str):
        self._ylabel_right = value

    @property
    def legend_visible(self) -> bool:
        return self._legend_visible

    @legend_visible.setter
    def legend_visible(self, value: bool):
        self._legend_visible = value

    @property
    def grid(self) -> bool:
        return self._grid

    @grid.setter
    def grid(self, value: bool):
        self._grid = value

    @property
    def height_ratio(self) -> int:
        return self._height_ratio

    @height_ratio.setter
    def height_ratio(self, value: int):
        if 1 <= value <= 10:
            self._height_ratio = value

    @property
    def xlim(self) -> float:
        # NOTE: 仮実装
        # ax.set_xlim((-2, 2))
        return 0.0

    @property
    def ylim(self) -> float:
        # NOTE: 仮実装
        # ax.set_ylim((-2, 2))
        return 0.0

    @property
    def candle(self) -> Candle:
        return self._candle

    @candle.setter
    def candle(self, value: Candle):
        self._candle = value

    @property
    def indicators_left(self) -> List[Indicator]:
        return self._indicators_left

    @indicators_left.setter
    def indicators_left(self, value: List[Indicator]):
        self._indicators_left = value

    @property
    def indicators_right(self) -> List[Indicator]:
        return self._indicators_right

    @indicators_right.setter
    def indicators_right(self, value: List[Indicator]):
        self._indicators_right = value

    @property
    def plt_axes_left(self) -> "AxesSubplot":
        # matplotlib.axes._subplots.AxesSubplot
        return self._plt_axes_left

    @plt_axes_left.setter
    def plt_axes_left(self, value: "AxesSubplot"):
        self._plt_axes_left = value

    @property
    def plt_axes_right(self) -> "AxesSubplot":
        # matplotlib.axes._subplots.AxesSubplot
        return self._plt_axes_right

    @plt_axes_right.setter
    def plt_axes_right(self, value: "AxesSubplot"):
        self._plt_axes_right = value

    @property
    def plt_candle_handler(self) -> Tuple["LineCollection", "PolyCollections"]:
        # (LineCollection, PolyCollections)
        return self._plt_candle_handler

    @plt_candle_handler.setter
    def plt_candle_handler(self, value: Tuple["LineCollection", "PolyCollections"]):
        self._plt_candle_handler = value

    @property
    def plt_indicator_left_handlers(self) -> List["Line2D"]:
        # matplotlib.lines.Line2D
        return self._plt_indicator_left_handlers

    @plt_indicator_left_handlers.setter
    def plt_indicator_left_handlers(self, value: List["Line2D"]):
        self._plt_indicator_left_handlers = value

    @property
    def plt_indicator_right_handlers(self) -> List["Line2D"]:
        # matplotlib.lines.Line2D
        return self._plt_indicator_right_handlers

    @plt_indicator_right_handlers.setter
    def plt_indicator_right_handlers(self, value: List["Line2D"]):
        self._plt_indicator_right_handlers = value


class Chart:
    """
    チャートを表示するクラス
    """

    def __init__(self):
        self._windows = []

    def add_window(self, window: ChartWindow):
        """
        ウインドウを追加する
        """
        self._windows.append(window)

    def show(self):
        """
        チャートを表示する
        """

        # 図表
        fig = plt.figure(figsize=(12, 6))
        fig.canvas.set_window_title("MagicTrader")

        # 図表のレイアウト
        gs_master = GridSpec(
            nrows=len(self._windows), ncols=1,
            height_ratios=[x.height_ratio for x in self._windows]
        )

        # 基準座標軸
        basis_ax = None

        for idx_win, window in enumerate(self._windows):

            # 座標軸のレイアウト
            gs_sub = GridSpecFromSubplotSpec(
                nrows=1, ncols=1,
                subplot_spec=gs_master[idx_win, 0]
            )

            # 座標軸(左)
            ax_left = None
            if basis_ax:
                ax_left = fig.add_subplot(gs_sub[:, :], sharex=basis_ax)
            else:
                ax_left = fig.add_subplot(gs_sub[:, :])
                basis_ax = ax_left
            window.plt_axes = ax_left

            # 座標軸(右)
            ax_right = ax_left.twinx()
            window.plt_axes_right = ax_right

            # タイトル
            if window.title != "":
                ax_left.set_title(window.title)

            # X軸ラベル
            if window.xlabel != "":
                ax_left.set_xlabel(window.xlabel)

            # Y軸ラベル(左)
            if window.ylabel_left != "":
                ax_left.set_ylabel(window.ylabel_left)

            # Y軸ラベル(右)
            if window.ylabel_right != "":
                ax_right.set_ylabel(window.ylabel_right)

            # グリッド
            ax_left.grid(window.grid)

            # ローソク足
            if window.candle:
                lines, polys = mpf.candlestick2_ohlc(
                    ax_left,
                    window.candle.opens,
                    window.candle.highs,
                    window.candle.lows,
                    window.candle.closes,
                    width=0.8, colorup='r', colordown='b', alpha=0.1
                )
                window.plt_candle_handler = (lines, polys)

            # インディケータ(左)
            for indicator in window.indicators_left:
                lines, = ax_left.plot(
                    indicator.prices, label=indicator.label, **indicator.style
                )
                window.plt_indicator_left_handlers.append(lines)

            # インディケータ(右)
            for indicator in window.indicators_right:
                lines, = ax_right.plot(
                    indicator.prices, label=indicator.label, **indicator.style
                )
                window.plt_indicator_right_handlers.append(lines)

            # レジェンド
            if window.legend_visible:
                h1, l1 = ax_left.get_legend_handles_labels()
                h2, l2 = ax_right.get_legend_handles_labels()
                ax_right.legend(h1+h2, l1+l2, loc="upper left")

            # 軸の範囲(左)
            if window.candle:
                # ローソク足の最低価格～最高価格とする
                ax_left.set_ylim(min(window.candle.lows), max(window.candle.highs))
                ax_left.set_xlim(0, len(window.candle.times))
            else:
                if len(window.indicators_left) > 0:
                    # インディケーターの最低価格～最高価格とする
                    min_price = 0
                    max_price = 0
                    for indicator in window.indicators_left:
                        wk = max(indicator.prices)
                        if wk > max_price:
                            max_price = wk
                        wk = min(indicator.prices)
                        if wk < min_price:
                            min_price = wk
                    ax_left.set_ylim(min_price, max_price)

            # 軸の範囲(右)
            if len(window.indicators_right) > 0:
                # インディケーターの最低価格～最高価格とする
                min_price = 0
                max_price = 0
                for indicator in window.indicators_right:
                    wk = max(indicator.prices)
                    if wk > max_price:
                        max_price = wk
                    wk = min(indicator.prices)
                    if wk < min_price:
                        min_price = wk
                ax_right.set_ylim(min_price, max_price)

        plt.tight_layout()
        plt.pause(0.1)

    def refresh(self):
        """
        チャートの表示を更新する
        """

        for window in self._windows:

            # 座標軸(左)
            ax_left = window.plt_axes

            # 座標軸(右)
            ax_right = window.plt_axes_right

            # タイトル
            if window.title != "":
                ax_left.set_title(window.title)

            # X軸ラベル
            if window.xlabel != "":
                ax_left.set_xlabel(window.xlabel)

            # Y軸ラベル(左)
            if window.ylabel_left != "":
                ax_left.set_ylabel(window.ylabel_left)

            # Y軸ラベル(右)
            if window.ylabel_right != "":
                ax_right.set_ylabel(window.ylabel_right)

            # グリッド
            ax_left.grid(window.grid)

            # ローソク足
            if window.candle:
                lines, polys = window.plt_candle_handler
                self._update_candlestick2_ohlc(
                    ax_left, lines, polys,
                    window.candle.opens,
                    window.candle.highs,
                    window.candle.lows,
                    window.candle.closes,
                    width=0.8, colorup='r', colordown='b', alpha=0.1
                )

            # インディケータ(左)
            for idx, indicator in enumerate(window.indicators_left):
                lines = window.plt_indicator_left_handlers[idx]
                lines.set_ydata(indicator.prices)

            # インディケータ(右)
            for idx, indicator in enumerate(window.indicators_right):
                lines = window.plt_indicator_right_handlers[idx]
                lines.set_ydata(indicator.prices)

            # レジェンド
            if window.legend_visible:
                h1, l1 = ax_left.get_legend_handles_labels()
                h2, l2 = ax_right.get_legend_handles_labels()
                ax_right.legend(h1+h2, l1+l2, loc="upper left")

            # 軸の範囲(左)
            if window.candle:
                # ローソク足の最低価格～最高価格とする
                ax_left.set_ylim(min(window.candle.lows), max(window.candle.highs))
                ax_left.set_xlim(0, len(window.candle.times))
            else:
                # インディケーターの最低価格～最高価格とする
                min_price = 0
                max_price = 0
                for indicator in window.indicators_left:
                    wk = max(indicator.prices)
                    if wk > max_price:
                        max_price = wk
                    wk = min(indicator.prices)
                    if wk < min_price:
                        min_price = wk
                ax_left.set_ylim(min_price, max_price)

            # 軸の範囲(右)
            if len(window.indicators_right) > 0:
                # インディケーターの最低価格～最高価格とする
                min_price = 0
                max_price = 0
                for indicator in window.indicators_right:
                    wk = max(indicator.prices)
                    if wk > max_price:
                        max_price = wk
                    wk = min(indicator.prices)
                    if wk < min_price:
                        min_price = wk
                ax_right.set_ylim(min_price, max_price)

        plt.tight_layout()
        plt.pause(0.1)

    def close(self):
        pass

    def save_as_png(self, pict_path: str):
        plt.savefig(pict_path)

    def _update_candlestick2_ohlc(self, ax, lines, polys, opens, highs, lows, closes,
                                  width=4, colorup='k', colordown='r', alpha=0.75):

        delta = width / 2.
        barVerts = [((i - delta, open),
                     (i - delta, close),
                     (i + delta, close),
                     (i + delta, open))
                    for i, open, close in zip(xrange(len(opens)), opens, closes)
                    if open != -1 and close != -1]

        rangeSegments = [((i, low), (i, high))
                         for i, low, high in zip(xrange(len(lows)), lows, highs)
                         if low != -1]

        colorup = mcolors.to_rgba(colorup, alpha)
        colordown = mcolors.to_rgba(colordown, alpha)
        colord = {True: colorup, False: colordown}
        colors = [colord[open < close]
                  for open, close in zip(opens, closes)
                  if open != -1 and close != -1]

        minx, maxx = 0, len(rangeSegments)
        miny = min([low for low in lows if low != -1])
        maxy = max([high for high in highs if high != -1])

        corners = (minx, miny), (maxx, maxy)
        ax.update_datalim(corners)
        ax.autoscale_view()

        lines.set_verts(rangeSegments)
        lines.set_color(colors)
        polys.set_verts(barVerts)
        polys.set_color(colors)
