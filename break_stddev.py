from datetime import datetime

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBBANDS
from magictrader.indicator import RSI, SMA, BBANDS, ADX, STDDEV, ENVELOPE
from magictrader.terminal import TradeTerminal
from magictrader.trade import Position, PositionRepository


class ScoreBoard:
    pass


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

        # テクニカルインディケーターを作成する

        # SMA
        sma_fast = SMA(feeder, 5, "sma_fast")
        sma_middle = SMA(feeder, 21, "sma_middle")
        sma_slow = SMA(feeder, 89, "sma_slow")

        # BBANDS
        bb_p3 = BBANDS(feeder, 21, 3, ModeBBANDS.UPPER, "bb_p3")
        bb_p2 = BBANDS(feeder, 21, 2, ModeBBANDS.UPPER, "bb_p2")
        bb_p1 = BBANDS(feeder, 21, 1, ModeBBANDS.UPPER, "bb_p1")
        bb_md = BBANDS(feeder, 21, 1, ModeBBANDS.MIDDLE, "bb_midle")
        bb_m1 = BBANDS(feeder, 21, 1, ModeBBANDS.LOWER, "bb_m1")
        bb_m2 = BBANDS(feeder, 21, 2, ModeBBANDS.LOWER, "bb_m2")
        bb_m3 = BBANDS(feeder, 21, 3, ModeBBANDS.LOWER, "bb_m3")

        # ADX
        adx_fast = ADX(feeder, 13, "adx_fast")
        adx_fast.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        adx_slow = ADX(feeder, 26, "adx_slow")
        adx_slow.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}

        # STDDEV
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ENVELOPE
        dev_rate1 = 0.011
        dev_rate2 = 0.015
        env_u2 = ENVELOPE(feeder, 26, dev_rate2, "env_u2")
        env_u2.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}
        env_u1 = ENVELOPE(feeder, 26, dev_rate1, "env_u1")
        env_u1.style = {"linestyle": "dashdot", "color": "grey", "linewidth": 0.5, "alpha": 1}
        env_md = ENVELOPE(feeder, 26, 0, "env_md")
        env_md.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}
        env_l1 = ENVELOPE(feeder, 26, -dev_rate1, "env_l1")
        env_l1.style = {"linestyle": "dashdot", "color": "grey", "linewidth": 0.5, "alpha": 1}
        env_l2 = ENVELOPE(feeder, 26, -dev_rate2, "env_l2")
        env_l2.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.legend_visible = False
        window_main.indicators_left.extend(
            [sma_fast, sma_middle, sma_slow,
             bb_p3, bb_p2, bb_p1, bb_md, bb_m1, bb_m2, bb_m3,
             env_u2, env_u1, env_md, env_l1, env_l2]
        )

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.extend([adx_fast, adx_slow])
        window_sub.indicators_right.append(stddev)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        # on_tickイベントに受け渡すデータを格納する
        data_bag["sma_fast"] = sma_fast
        data_bag["sma_middle"] = sma_middle
        data_bag["sma_slow"] = sma_slow
        data_bag["bb_p3"] = bb_p3
        data_bag["bb_p2"] = bb_p2
        data_bag["bb_p1"] = bb_p1
        data_bag["bb_md"] = bb_md
        data_bag["bb_m1"] = bb_m1
        data_bag["bb_m2"] = bb_m2
        data_bag["bb_m3"] = bb_m3
        data_bag["adx_fast"] = adx_fast
        data_bag["adx_slow"] = adx_slow
        data_bag["stddev"] = stddev
        data_bag["env_u2"] = env_u2
        data_bag["env_u1"] = env_u1
        data_bag["env_md"] = env_md
        data_bag["env_l1"] = env_l1
        data_bag["env_l2"] = env_l2

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

        # 受け渡されたデータを引き出す
        sma_fast = data_bag["sma_fast"]
        sma_middle = data_bag["sma_middle"]
        sma_slow = data_bag["sma_slow"]
        bb_p3 = data_bag["bb_p3"]
        bb_p2 = data_bag["bb_p2"]
        bb_p1 = data_bag["bb_p1"]
        bb_md = data_bag["bb_md"]
        bb_m1 = data_bag["bb_m1"]
        bb_m2 = data_bag["bb_m2"]
        bb_m3 = data_bag["bb_m3"]
        adx_fast = data_bag["adx_fast"]
        adx_slow = data_bag["adx_slow"]
        stddev = data_bag["stddev"]
        env_u2 = data_bag["env_u2"]
        env_u1 = data_bag["env_u1"]
        env_md = data_bag["env_md"]
        env_l1 = data_bag["env_l1"]
        env_l2 = data_bag["env_l2"]

        # ゴールデンクロスを判定する
        if sma_fast.prices[-3] < sma_slow.prices[-3]  \
                and sma_fast.prices[-2] > sma_slow.prices[-2]:

            # ロングポジションを開く
            position = position_repository.create_position()
            position.open(candle.times[-1], "buy", candle.closes[-1], 1, "open: golden cross")

        # デッドクロスを判定する
        if sma_fast.prices[-3] > sma_slow.prices[-3]  \
                and sma_fast.prices[-2] < sma_slow.prices[-2]:

            # 未決済のロングポジションを閉じる
            long_positions = list(filter(lambda x: x.open_action == "buy" and x.is_closed == False, position_repository.positions))
            for long_position in long_positions:
                long_position.close(candle.times[-1], candle.closes[-1], "close: golden cross")

    def _on_opening_position(self, position: Position, position_repository: PositionRepository) -> (bool, float, float):
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
        (bool, float, float)
            1: ポジションを一部でも開くことに成功した場合Trueを返します。
            2: 実際の約定価格を返します。
            3: 実際の約定数量を返します。
        """
        return True, position.open_price, position.order_amount

    def _on_closing_position(self, position: Position, position_repository: PositionRepository) -> float:
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
    # mytrade = MyTradeTerminal("btc_jpy", "5m", "practice")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "5m", "forwardtest")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "4h", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))

    mytrade.run()
