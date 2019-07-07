from typing import List, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mpl_finance as mpf
from six.moves import xrange, zip

from magictrader.candle import Candle
from magictrader.indicator import Indicator


class Chart:
    """
    Chartを表示するクラス
    """

    def __init__(self, title: str, candle: Candle, indicators: List[Indicator], sub_windows: List[Tuple[List[Indicator], List[Indicator]]] = []):
        """
        チャートを初期化し、表示します。

        Parameters
        ----------
        title : str
            タイトル
        candle : Candle
            ローソク足
        indicators : List[indicator]
            インディケーター
        sub_windows : List[Tuple[List[Indicator], List[Indicator]]]
            サブウィンドウ

            サブウィンドウに下記を表示する場合
            1. sub window 1の左にindicatorAB、右にCを表示する。
            2. sub window 2の左にindicatorX、右にYZを表示する。

            引数に下記の値を渡します。
            [([IndicatorA, IndicatorB], [IndicatorC]),
             ([IndicatorX], [IndicatorZ, IndicatorY])]
        """

        rows = 1 + len(sub_windows)
        height_ratios = [3]
        height_ratios.extend([1]*len(sub_windows))
        self._fig, self._ax = plt.subplots(
            nrows=rows, ncols=1, figsize=(12, 6), sharex=True, gridspec_kw={'height_ratios': height_ratios}
        )

        #######################################################
        # メインウィンドウを描画
        #######################################################

        # ローソク足を描画
        self._r, self._b = mpf.candlestick2_ohlc(
            self._ax[0], candle.opens, candle.highs, candle.lows, candle.closes, candle.width, colorup='r', colordown='b', alpha=0.1
        )

        # インディケーターを描画
        self._indicator_handlers = []
        for indicator in indicators:
            indicator_handler, = self._ax[0].plot(
                indicator.prices, label=indicator.label, **indicator.style
            )
            self._indicator_handlers.append(indicator_handler)

        # タイトルを描画
        self._ax[0].set_title(title)

        # # 日時を描画
        # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
        # self._fig.autofmt_xdate()

        #######################################################
        # サブウィンドウを描画
        #######################################################

        # サブウィンドウを描画
        self._ax_lefts = []
        self._ax_rights = []
        self._oscillator_handles = [[[], []]] * len(sub_windows)
        for win_idx, sub_window in enumerate(sub_windows):

            ax_left = self._ax[1 + win_idx]     # 左Y軸のハンドル
            ax_right = ax_left.twinx()          # 右Y軸のハンドル
            self._ax_lefts.append(ax_left)
            self._ax_rights.append(ax_right)

            # 左Y軸に表示するインディケーター
            for left_idx, oscillator in enumerate(sub_window[0]):
                oscillator_handle, = ax_left.plot(
                    oscillator.prices, label=oscillator.label, **oscillator.style
                )
                self._oscillator_handles[win_idx][0].append(oscillator_handle)

            # 右Y軸に表示するインディケーター
            for right_idx, oscillator in enumerate(sub_window[1]):
                oscillator_handle, = ax_right.plot(
                    oscillator.prices, label=oscillator.label, **oscillator.style
                )
                self._oscillator_handles[win_idx][1].append(oscillator_handle)

            # レジェンドを表示する
            h1, l1 = ax_left.get_legend_handles_labels()
            h2, l2 = ax_right.get_legend_handles_labels()
            ax_right.legend(h1+h2, l1+l2, loc="upper left")

            # # Y軸ラベルを表示する
            # ax_left.set_ylabel("left_y_label")
            # ax_right.set_ylabel("right_y_label")
            # self._ax[1+win_idx].grid(True)

        plt.tight_layout()
        plt.pause(0.1)

    def update(self, title: str, candle: Candle, indicators: List[Indicator], sub_windows: List[Tuple[List[Indicator], List[Indicator]]] = []):
        """
        チャートを更新します。

        Parameters
        ----------
        title : str
            タイトル
        candle : Candle
            ローソク足
        indicators : List[indicator]
            インディケーター
        sub_windows : List[Tuple[List[Indicator], List[Indicator]]]
            サブウィンドウ

            サブウィンドウに下記を表示する場合
            1. sub window 1の左にindicatorAB、右にCを表示する。
            2. sub window 2の左にindicatorX、右にYZを表示する。

            引数に下記の値を渡します。
            [([IndicatorA, IndicatorB], [IndicatorC]),
             ([IndicatorX], [IndicatorZ, IndicatorY])]
        """

        #######################################################
        # メインウィンドウを再描画
        #######################################################

        delta = candle.width / 2.
        barVerts = [((i - delta, open),
                     (i - delta, close),
                     (i + delta, close),
                     (i + delta, open))
                    for i, open, close in zip(xrange(len(candle.opens)), candle.opens, candle.closes)
                    if open != -1 and close != -1]

        rangeSegments = [((i, low), (i, high))
                         for i, low, high in zip(xrange(len(candle.lows)), candle.lows, candle.highs)
                         if low != -1]

        minx, maxx = 0, len(rangeSegments)
        miny = min([low for low in candle.lows if low != -1])
        maxy = max([high for high in candle.highs if high != -1])

        corners = (minx, miny), (maxx, maxy)
        self._ax[0].update_datalim(corners)
        self._ax[0].autoscale_view()

        # ローソク足を描画
        self._b.set_verts(barVerts)
        self._r.set_verts(rangeSegments)
        self._ax[0].set_xlim(0, len(rangeSegments))
        self._ax[0].set_ylim(min(candle.lows), max(candle.highs))
        self._ax[0].autoscale_view()

        # インディケーターを描画
        for idx, indicator in enumerate(indicators):
            self._indicator_handlers[idx].set_ydata(indicator.prices)

        # タイトルを描画
        self._ax[0].set_title(title)

        # # 日時を描画
        # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
        # self._fig.autofmt_xdate()

        #######################################################
        # サブウィンドウを再描画
        #######################################################

        # サブウィンドウを描画
        for win_idx, sub_window in enumerate(sub_windows):
            max_y_left = 0.0
            max_y_right = 0.0

            # 左Y軸に表示するオシレーター
            for left_idx, oscillator in enumerate(sub_window[0]):
                self._oscillator_handles[win_idx][0][left_idx].set_ydata(oscillator.prices)
                max_y_left = max(oscillator.prices) if max(oscillator.prices) > max_y_left else max_y_left

            # 右Y軸に表示するオシレーター
            for right_idx, oscillator in enumerate(sub_window[1]):
                self._oscillator_handles[win_idx][1][right_idx].set_ydata(oscillator.prices)
                max_y_right = max(oscillator.prices) if max(oscillator.prices) > max_y_right else max_y_right

            self._ax_lefts[win_idx].set_ylim(0, max_y_left)
            self._ax_rights[win_idx].set_ylim(0, max_y_right)
            self._ax_lefts[win_idx].autoscale_view()
            self._ax_rights[win_idx].autoscale_view()

        plt.tight_layout()
        plt.pause(0.1)

    def save_as_png(self, pict_path: str):
        plt.savefig(pict_path)
