from datetime import datetime, timedelta
from itertools import groupby

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBAND, Period
from magictrader.indicator import ADX, ATRBAND, BBANDS, EMA, STDDEV
from magictrader.position import Position, PositionRepository
from magictrader.terminal import TradeTerminal


class SignalHistory:
    """
    シグナル履歴

    一時的な相場変動によるノイズを取り除くため、
    一定期間履歴を取得し、その最大多数をシグナルとして利用します。
    履歴の数は取引時間軸に応じて適切に変更してください。
    """

    def __init__(self, history_count: int):
        self.history_update_count = 0
        self.history_count = history_count
        self.ema_fast_status = ["neutral"] * history_count
        self.bband_status = ["neutral"] * history_count
        self.bband_width_status = ["neutral"] * history_count
        self.adx_fast_status = ["neutral"] * history_count
        self.adx_slow_status = ["neutral"] * history_count
        self.stddev_status = ["neutral"] * history_count
        self.dip_ready = True
        self.rip_ready = True
        self.touch_major_high = False
        self.touch_major_low = False

    def complete_updating_signals(self):
        if self.history_update_count < 9999:
            self.history_update_count += 1

    @property
    def signal_available(self) -> bool:
        if self.history_update_count >= self.history_count:
            return True
        else:
            return False

    @property
    def ema_fast_status_summary(self) -> str:
        max_count = 1
        max_item = self.ema_fast_status[-1]
        sorted_items = sorted(self.ema_fast_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item

    @property
    def bband_status_summary(self) -> str:
        max_count = 1
        max_item = self.bband_status[-1]
        sorted_items = sorted(self.bband_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item

    @property
    def bband_width_status_summary(self) -> str:
        max_count = 1
        max_item = self.bband_width_status[-1]
        sorted_items = sorted(self.bband_width_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item

    @property
    def adx_fast_status_summary(self) -> str:
        max_count = 1
        max_item = self.adx_fast_status[-1]
        sorted_items = sorted(self.adx_fast_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item

    @property
    def adx_slow_status_summary(self) -> str:
        max_count = 1
        max_item = self.adx_slow_status[-1]
        sorted_items = sorted(self.adx_slow_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item

    @property
    def stddev_status_summary(self) -> str:
        max_count = 1
        max_item = self.stddev_status[-1]
        sorted_items = sorted(self.stddev_status)
        for key, group in groupby(sorted_items):
            group_count = len(list(group))
            if group_count > max_count:
                max_item = key
                max_count = group_count
        return max_item


class MyTradeTerminal(TradeTerminal):

    def _on_init(self, feeder: CandleFeeder, chart: Chart, window_main: ChartWindow, data_bag: dict):
        """
        on_initイベントでは、
        トレードで使用するテクニカルインディケーターを作成したり、
        チャートの画面構成を定義するための初期化処理を行います。

        Parameters
        ----------
        feeder : CandleFeeder
            ローソク足のデータを提供するフィーダーです。
        chart : Chart
            チャート画面本体です。
        window_main : ChartWindow
            チャートのメイン画面です。
        data_bag : dict
            on_tickイベントに受け渡したいデータを格納します。
        """

        ##################################################
        # テクニカルインディケーターを作成する
        ##################################################

        # SMA
        ema_fast = EMA(feeder, 5, "ema_fast")
        ema_middle = EMA(feeder, 21, "ema_middle")
        ema_slow = EMA(feeder, 89, "ema_slow")

        # BBANDS
        bb_p3 = BBANDS(feeder, 21, 3, ModeBAND.UPPER, "bband_p3")
        bb_p2 = BBANDS(feeder, 21, 2, ModeBAND.UPPER, "bband_p2")
        bb_p1 = BBANDS(feeder, 21, 1, ModeBAND.UPPER, "bband_p1")
        bb_md = BBANDS(feeder, 21, 1, ModeBAND.MIDDLE, "bband_middle")
        bb_m1 = BBANDS(feeder, 21, 1, ModeBAND.LOWER, "bband_m1")
        bb_m2 = BBANDS(feeder, 21, 2, ModeBAND.LOWER, "bband_m2")
        bb_m3 = BBANDS(feeder, 21, 3, ModeBAND.LOWER, "bband_m3")
        bb_wd = STDDEV(feeder, 21, 1, "bband_width")
        bb_wd.style = {"linestyle": "solid", "color": "magenta", "linewidth": 1, "alpha": 1}

        # ADX
        adx_fast = ADX(feeder, 8, "adx_fast")
        adx_fast.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        adx_slow = ADX(feeder, 14, "adx_slow")
        adx_slow.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}

        # STDDEV
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ATRBAND
        atrb_u1 = ATRBAND(feeder, 49, 14, 2, ModeBAND.UPPER, "atr_band_p1")
        atrb_u1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}
        atrb_l1 = ATRBAND(feeder, 49, 14, 2, ModeBAND.LOWER, "atr_band_m1")
        atrb_l1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}

        ##################################################
        # チャートの画面構成を定義する
        ##################################################

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        # window_main.legend_visible = False
        window_main.indicators_left.extend(
            [ema_fast, ema_middle, ema_slow,
             bb_p3, bb_p2, bb_p1, bb_md, bb_m1, bb_m2, bb_m3,
             atrb_u1, atrb_l1]
        )

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.extend([bb_wd, stddev])
        window_sub.indicators_right.extend([adx_fast, adx_slow])

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        ##################################################
        # on_tickイベントに受け渡すデータを格納する
        ##################################################

        # テクニカルインディケーター
        data_bag["ema_fast"] = ema_fast
        data_bag["ema_middle"] = ema_middle
        data_bag["ema_slow"] = ema_slow
        data_bag["bb_p3"] = bb_p3
        data_bag["bb_p2"] = bb_p2
        data_bag["bb_p1"] = bb_p1
        data_bag["bb_md"] = bb_md
        data_bag["bb_m1"] = bb_m1
        data_bag["bb_m2"] = bb_m2
        data_bag["bb_m3"] = bb_m3
        data_bag["bb_wd"] = bb_wd
        data_bag["atrb_u1"] = atrb_u1
        data_bag["atrb_l1"] = atrb_l1
        data_bag["adx_fast"] = adx_fast
        data_bag["adx_slow"] = adx_slow
        data_bag["stddev"] = stddev

        # シグナル履歴
        history_count = 80 if self._trade_mode in ["practice", "forwardtest"] else 10
        data_bag["signal_history"] = SignalHistory(history_count)

    def _on_tick(self, candle: Candle, data_bag: dict, position_repository: PositionRepository, is_newbar: bool):
        """
        on_tickイベントは、ローソク足のデータが更新されるたびに呼び出されます。

        Tips
        ----------
        ローソク足のデータ取得方法
        ・時刻はcandle.times[n]で取得できます。
        ・始値はcandle.opens[n]で取得できます。
        ・高値はcandle.highs[n]で取得できます。
        ・安値はcandle.lows[n]で取得できます。
        ・終値はcandle.closes[n]で取得できます。
        ※これらは時系列順のリストであり、nは0~199の数値を取ります。

        テクニカルインディケーターのデータ取得方法
        ・時刻はindicator.times[n]で取得できます。
        ・価格はindicator.prices[n]で取得できます。
        ※これらは時系列順のリストであり、nは0~199の数値を取ります。

        Parameters
        ----------
        candle : Candle
            ローソク足(OHLC)です。
        data_bag : dict
            on_initイベントから受け渡されたデータが格納されています。
            また、次のon_tickイベントに受け渡したいデータを格納します。
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ
        is_newbar : bool
            新しい足が追加された最初の呼び出し時に１度だけTrueとなります。
        """

        ##################################################
        # 受け渡されたデータを引き出す
        ##################################################

        # テクニカルインディケーター
        ema_fast = data_bag["ema_fast"]
        ema_middle = data_bag["ema_middle"]
        ema_slow = data_bag["ema_slow"]
        bb_p3 = data_bag["bb_p3"]
        bb_p2 = data_bag["bb_p2"]
        bb_p1 = data_bag["bb_p1"]
        bb_md = data_bag["bb_md"]
        bb_m1 = data_bag["bb_m1"]
        bb_m2 = data_bag["bb_m2"]
        bb_m3 = data_bag["bb_m3"]
        bb_wd = data_bag["bb_wd"]
        atrb_u1 = data_bag["atrb_u1"]
        atrb_l1 = data_bag["atrb_l1"]
        adx_fast = data_bag["adx_fast"]
        adx_slow = data_bag["adx_slow"]
        stddev = data_bag["stddev"]

        # シグナル履歴
        signal = data_bag["signal_history"]

        # 買いストラテジーのポジション
        long_position = None
        for p in position_repository.get_open_positions("buy"):
            long_position = p
            break

        # 売りストラテジーのポジション
        short_position = None
        for p in position_repository.get_open_positions("sell"):
            short_position = p
            break

        ##################################################
        # シグナルの検出
        ##################################################

        ema_fast_status = "neutral"
        bband_status = "neutral"
        bband_width_status = "neutral"
        adx_fast_status = "neutral"
        adx_slow_status = "neutral"
        stddev_status = "neutral"

        # SMA
        idx_from = -4
        min_price_idx = ema_fast.prices.index(min(ema_fast.prices[idx_from:-1]))
        max_price_idx = ema_fast.prices.index(max(ema_fast.prices[idx_from:-1]))

        if ema_fast.prices[-1] > max(ema_fast.prices[idx_from:-1]) \
                and max_price_idx < max_price_idx:
            ema_fast_status = "jumpup"

        if ema_fast.prices[-1] > max(ema_fast.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            ema_fast_status = "bull"

        if ema_fast.prices[-1] < max(ema_fast.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            ema_fast_status = "peakout"

        if ema_fast.prices[-1] < max(ema_fast.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            ema_fast_status = "bear"

        # BBAND
        if candle.closes[-1] > bb_p1.prices[-1]:
            if candle.closes[-2] < bb_p1.prices[-2]:
                bband_status = "bull_break"
            else:
                bband_status = "bull"

        if candle.closes[-1] < bb_m1.prices[-1]:
            if candle.closes[-2] > bb_m1.prices[-2]:
                bband_status = "bear_break"
            else:
                bband_status = "bear"

        # BBAND_WIDTH
        idx_from = -4
        min_price_idx = bb_wd.prices.index(min(bb_wd.prices[idx_from:-1]))
        max_price_idx = bb_wd.prices.index(max(bb_wd.prices[idx_from:-1]))

        if bb_wd.prices[-1] > max(bb_wd.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            bband_width_status = "jumpup"

        if bb_wd.prices[-1] > max(bb_wd.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            bband_width_status = "bull"

        if bb_wd.prices[-1] < max(bb_wd.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            bband_width_status = "peakout"

        if bb_wd.prices[-1] < max(bb_wd.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            bband_width_status = "bear"

        # ADX短期
        idx_from = -4
        min_price_idx = adx_fast.prices.index(min(adx_fast.prices[idx_from:-1]))
        max_price_idx = adx_fast.prices.index(max(adx_fast.prices[idx_from:-1]))

        if adx_fast.prices[-1] > max(adx_fast.prices[idx_from:-1]) \
                and max_price_idx < max_price_idx:
            adx_fast_status = "jumpup"

        if adx_fast.prices[-1] > max(adx_fast.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            adx_fast_status = "bull"

        if adx_fast.prices[-1] < max(adx_fast.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            adx_fast_status = "peakout"

        if adx_fast.prices[-1] < max(adx_fast.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            adx_fast_status = "bear"

        # ADX長期
        idx_from = -4
        min_price_idx = adx_slow.prices.index(min(adx_slow.prices[idx_from:-1]))
        max_price_idx = adx_slow.prices.index(max(adx_slow.prices[idx_from:-1]))

        if adx_slow.prices[-1] >= max(adx_slow.prices[idx_from:-1]) \
                and min_price_idx > max_price_idx:
            adx_slow_status = "jumpup"

        if adx_slow.prices[-1] >= max(adx_slow.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            adx_slow_status = "bull"

        if adx_slow.prices[-1] < max(adx_slow.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            adx_slow_status = "peakout"

        if adx_slow.prices[-1] < max(adx_slow.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            adx_slow_status = "bear"

        # STDDEV
        idx_from = -4
        min_price_idx = stddev.prices.index(min(stddev.prices[idx_from:-1]))
        max_price_idx = stddev.prices.index(max(stddev.prices[idx_from:-1]))

        if stddev.prices[-1] >= max(stddev.prices[idx_from:-1]) \
                and min_price_idx > max_price_idx:
            stddev_status = "jumpup"

        if stddev.prices[-1] >= max(stddev.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            stddev_status = "bull"

        if stddev.prices[-1] < max(stddev.prices[idx_from:-1]) \
                and max_price_idx > min_price_idx:
            stddev_status = "peakout"

        if stddev.prices[-1] < max(stddev.prices[idx_from:-1]) \
                and max_price_idx < min_price_idx:
            stddev_status = "bear"

        # 買いスタンバイをON
        if ema_fast_status in ["peakout", "bear"]:
            signal.dip_ready = True

        # 売りスタンバイをON
        if ema_fast_status in ["jumpup", "bull"]:
            signal.rip_ready = True

        # 天井・大底フラグをOFF
        if bband_status in ["neutral"] \
                and adx_fast_status in ["neutral", "bear", "peakout"] \
                and adx_slow_status in ["neutral", "bear", "peakout"] \
                and stddev_status in ["neutral", "bear", "peakout"]:
            signal.touch_major_high = False
            signal.touch_major_low = False

        # シグナル履歴を最新化
        signal.ema_fast_status.append(ema_fast_status)
        del signal.ema_fast_status[0]
        signal.bband_status.append(bband_status)
        del signal.bband_status[0]
        signal.bband_width_status.append(bband_width_status)
        del signal.bband_width_status[0]
        signal.adx_fast_status.append(adx_fast_status)
        del signal.adx_fast_status[0]
        signal.adx_slow_status.append(adx_slow_status)
        del signal.adx_slow_status[0]
        signal.stddev_status.append(stddev_status)
        del signal.stddev_status[0]

        self._logger.info(
            "{}:{}:{}:{}:{}:{}".format(candle.times[-1], bband_width_status, bband_status, adx_fast_status, adx_slow_status, stddev_status)
        )

        signal.complete_updating_signals()
        if not signal.signal_available:
            return

        ##################################################
        # 買いストラテジー
        ##################################################

        # エントリー：標準偏差順張り
        if not long_position:

            if not long_position and signal.dip_ready \
                    and not signal.touch_major_high \
                    and candle.closes[-2] >= ema_slow.prices[-2] \
                    and candle.closes[-1] >= ema_slow.prices[-1] \
                    and signal.bband_width_status_summary in ["jumpup", "bull"] \
                    and signal.bband_status_summary in ["bull", "bull_break"] \
                    and (int(signal.adx_fast_status_summary in ["jumpup", "bull"])
                         + int(signal.adx_slow_status_summary in ["jumpup", "bull"])
                         + int(signal.stddev_status_summary in ["jumpup", "bull"]) >= 2):
                # ポジション
                long_position = position_repository.create_position()
                long_position.open(candle.times[-1], "buy", candle.closes[-1], 1, "標準偏差順張り")
                # 買いスタンバイをOFF
                signal.dip_ready = False

        # イグジット：標準偏差順張り
        if long_position \
                and long_position.open_comment == "標準偏差順張り":

            # 利確：BB+1σ下抜け
            if not long_position.is_closed and long_position.hold_period >= 5:
                if candle.closes[-2] < bb_p1.prices[-2]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "+1σ下抜け")

            # 利確：標準偏差ピークアウト
            if not long_position.is_closed and long_position.hold_period >= 1:
                if candle.closes[-1] >= atrb_u1.prices[-1] \
                        and (int(signal.adx_fast_status_summary in ["neutral", "bear", "peakout"])
                             + int(signal.adx_slow_status_summary in ["neutral", "bear", "peakout"])
                             + int(signal.stddev_status_summary in ["neutral", "bear", "peakout"]) >= 2):
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "標準偏差ピークアウト")
                    # 天井フラグをON
                    signal.touch_major_high = True

            # 損切り：中期SMAタッチ
            if not long_position.is_closed and long_position.hold_period >= 1:
                if candle.closes[-1] < ema_middle.prices[-1]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "SMA中期タッチ")

        ##################################################
        # 売りストラテジー
        ##################################################

        # エントリー：標準偏差順張り
        if not short_position:

            if not short_position and signal.rip_ready \
                    and not signal.touch_major_low \
                    and candle.closes[-2] <= ema_slow.prices[-2] \
                    and candle.closes[-1] <= ema_slow.prices[-1] \
                    and signal.bband_width_status_summary in ["jumpup", "bull"] \
                    and signal.bband_status_summary in ["bear", "bear_break"] \
                    and (int(signal.adx_fast_status_summary in ["jumpup", "bull"])
                         + int(signal.adx_slow_status_summary in ["jumpup", "bull"])
                         + int(signal.stddev_status_summary in ["jumpup", "bull"]) >= 2):
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "標準偏差順張り")
                # 売りスタンバイをOFF
                signal.rip_ready = False

        # イグジット：標準偏差順張り
        if short_position \
                and short_position.open_comment == "標準偏差順張り":

            # 利確：BB+1σ下抜け
            if not short_position.is_closed and short_position.hold_period >= 5:
                if candle.closes[-2] > bb_m1.prices[-2]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "+1σ下抜け")

            # 利確：標準偏差ピークアウト
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-1] <= atrb_l1.prices[-1] \
                        and(int(signal.adx_fast_status_summary in ["neutral", "bear", "peakout"])
                            + int(signal.adx_slow_status_summary in ["neutral", "bear", "peakout"])
                            + int(signal.stddev_status_summary in ["neutral", "bear", "peakout"]) >= 2):
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "標準偏差ピークアウト")
                    # 大底フラグをON
                    signal.touch_major_low = True

            # 損切り：中期SMAタッチ
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-1] > ema_middle.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "SMA中期タッチ")

    def _on_position_opening(self, position: Position, position_repository: PositionRepository) -> (float, float, bool):
        """
        ポジションを開くときに呼び出されます。
        ポジションをどのように開くかを実装します。

        Parameters
        ----------
        position : Position
            オープンリクエストされたポジション
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ

        Returns
        -------
        (float, float, bool)
            1: 実際の約定価格を返します。
            2: 実際の約定数量を返します。
            3: ポジションを一部でも開くことに成功した場合はFalse、
               すべてキャンセルした場合はTrueを返します。
        """
        return position.open_price, position.order_amount, False

    def _on_position_closing(self, position: Position, position_repository: PositionRepository) -> float:
        """
        ポジションを閉じるときに呼び出されます。
        ポジションをどのように閉じるかを実装します。

        Parameters
        ----------
        position : Position
            クローズリクエストされたポジション
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ

        Returns
        -------
        float
            実際の約定価格を返します。
        """
        return position.close_price


if __name__ == "__main__":

    # 実践モードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "4h", "practice", terminal_name="break_stddev")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "forwardtest", terminal_name="break_stddev")
    # バックテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "backtest", datetime(2017, 4, 1), datetime(2019, 8, 3), terminal_name="break_stddev")

    mytrade.run()
