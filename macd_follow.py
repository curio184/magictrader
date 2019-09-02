from datetime import datetime

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBAND, ModeMACD
from magictrader.indicator import ATRBAND, EMA, MACD, HLine, SchaffTC
from magictrader.position import Position, PositionRepository
from magictrader.terminal import TradeTerminal


class SignalBoard:

    def __init__(self):
        self.stc_status = "neutral"
        self.dip_ready = True
        self.rip_ready = True


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

        # EMA
        ema_fast = EMA(feeder, 5, "ema_fast")
        ema_middle = EMA(feeder, 21, "ema_middle")
        ema_slow = EMA(feeder, 89, "ema_slow")

        # ATRBAND
        atrb_u1 = ATRBAND(feeder, 49, 14, 3, ModeBAND.UPPER, "atr_band_p1")
        atrb_u1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}
        atrb_l1 = ATRBAND(feeder, 49, 14, 3, ModeBAND.LOWER, "atr_band_m1")
        atrb_l1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}

        # MACD
        macd = MACD(feeder, 12, 26, 9, ModeMACD.MACD)
        macd_signal = MACD(feeder, 12, 26, 9, ModeMACD.SIGNAL)
        macd_histogram = MACD(feeder, 12, 26, 9, ModeMACD.HISTOGRAM)

        # Horizontal Line
        hline = HLine(feeder, 0, "zero_line")

        # Schaff Trend Cycle
        stc = SchaffTC(feeder)

        ##################################################
        # チャートの画面構成を定義する
        ##################################################

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.indicators_left.extend(
            [ema_fast, ema_middle, ema_slow,
             atrb_u1, atrb_l1]
        )

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub1 = ChartWindow()
        window_sub1.height_ratio = 1
        window_sub1.indicators_left.append(macd)
        window_sub1.indicators_left.append(macd_signal)
        window_sub1.indicators_left.append(macd_histogram)
        window_sub1.indicators_left.append(hline)

        window_sub2 = ChartWindow()
        window_sub2.height_ratio = 1
        window_sub2.indicators_left.append(stc)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub1)
        chart.add_window(window_sub2)

        ##################################################
        # on_tickイベントに受け渡すデータを格納する
        ##################################################

        # テクニカルインディケーター
        data_bag["ema_fast"] = ema_fast
        data_bag["ema_middle"] = ema_middle
        data_bag["ema_slow"] = ema_slow
        data_bag["atrb_u1"] = atrb_u1
        data_bag["atrb_l1"] = atrb_l1
        data_bag["macd"] = macd
        data_bag["macd_signal"] = macd_signal
        data_bag["macd_histogram"] = macd_histogram
        data_bag["stc"] = stc

        # シグナルボード
        data_bag["signal_board"] = SignalBoard()

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
        atrb_u1 = data_bag["atrb_u1"]
        atrb_l1 = data_bag["atrb_l1"]
        macd = data_bag["macd"]
        macd_signal = data_bag["macd_signal"]
        macd_histogram = data_bag["macd_histogram"]
        stc = data_bag["stc"]

        # シグナルボード
        signal = data_bag["signal_board"]

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

        macd_strength = 0

        # MACD
        idx_from = -5

        if macd.prices[-2] > 0 and macd_signal.prices[-2] > 0 and macd_histogram.prices[-2] > 0:
            macd_strength = int(macd.prices[-2] > max(macd.prices[idx_from:-2])) \
                + int(macd_signal.prices[-2] > max(macd_signal.prices[idx_from:-2]))\
                + int(macd_histogram.prices[-2] > max(macd_histogram.prices[idx_from:-2]))

        if macd.prices[-2] < 0 and macd_signal.prices[-2] < 0 and macd_histogram.prices[-2] < 0:
            macd_strength = - int(macd.prices[-2] < max(macd.prices[idx_from:-2])) \
                - int(macd_signal.prices[-2] < max(macd_signal.prices[idx_from:-2])) \
                - int(macd_histogram.prices[-2] < max(macd_histogram.prices[idx_from:-2]))

        # Schaff Trend Cycle
        idx_from = -5

        if signal.stc_status in ["bear", "neutral"]:
            if max(stc.prices[idx_from:-2]) < 0.1 \
                    and stc.prices[-2] >= 0.1:
                signal.stc_status = "bull"

        if signal.stc_status in ["bull", "neutral"]:
            if max(stc.prices[idx_from:-2]) > 0.9 \
                    and stc.prices[-2] <= 0.9:
                signal.stc_status = "bear"

        # 買いスタンバイをON
        # if stc.prices[-2] < 0.2:
        if stc.prices[-2] < 0.5:
            signal.dip_ready = True

        # 売りスタンバイをON
        # if stc.prices[-2] > 0.8:
        if stc.prices[-2] > 0.5:
            signal.rip_ready = True

        # シグナル履歴を最新化
        # signal.something.append(something)
        # del signal.something[0]

        self._logger.info(
            "{}:{}:{}:{}".format(candle.times[-1], macd_strength, signal.stc_status, stc.prices[-1])
        )

        ##################################################
        # 買いストラテジー
        ##################################################
        # エントリー：MACD順張り
        if not long_position:

            if not long_position and signal.dip_ready \
                    and signal.stc_status == "bull" \
                    and macd_strength == 3:
                # ポジション
                long_position = position_repository.create_position()
                long_position.open(candle.times[-1], "buy", candle.closes[-1], 1, "MACD順張り")
                # 買いスタンバイをOFF
                signal.dip_ready = False

        # イグジット：MACD順張り
        if long_position \
                and long_position.open_comment == "MACD順張り":

            # 利確：MACD収束
            if not long_position.is_closed \
                    and (signal.stc_status == "bear"
                         or macd_strength <= 2):

                # ポジション
                long_position.close(candle.times[-1], candle.closes[-1], "MACD収束")

            # 利確：ATRBAND上限
            if not long_position.is_closed \
                    and candle.closes[-1] >= atrb_u1.prices[-1] \
                    and stc.prices[-1] >= 0.95:

                # ポジション
                long_position.close(candle.times[-1], candle.closes[-1], "ATRBAND上限")

        ##################################################
        # 売りストラテジー
        ##################################################
        # エントリー：MACD順張り
        if not short_position:

            if not short_position and signal.rip_ready \
                and signal.stc_status == "bear" \
                    and macd_strength <= -3:
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "MACD順張り")
                # 売りスタンバイをOFF
                signal.rip_ready = False

        # イグジット：MACD順張り
        if short_position \
                and short_position.open_comment == "MACD順張り":

            # 利確：MACD収束
            if not short_position.is_closed \
                    and (signal.stc_status == "bull"
                         or macd_strength >= -2):
                # ポジション
                short_position.close(candle.times[-1], candle.closes[-1], "MACD収束")

            # 利確：ATR下限
            if not short_position.is_closed \
                    and candle.closes[-1] <= atrb_l1.prices[-1] \
                    and stc.prices[-1] <= 0.05:

                # ポジション
                short_position.close(candle.times[-1], candle.closes[-1], "ATR下限")

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
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "practice", terminal_name="macd_follow")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "forwardtest", terminal_name="macd_follow")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "4h", "backtest", datetime(2019, 6, 1), datetime(2019, 8, 30), terminal_name="macd_follow")

    mytrade.run()
