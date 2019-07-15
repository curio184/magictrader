from datetime import datetime

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.indicator import RSI, SMA
from magictrader.terminal import TradeTerminal
from magictrader.trade import Position, PositionRepository


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
        sma_fast = SMA(feeder, 5)           # 短期SMA
        sma_middle = SMA(feeder, 25)        # 中期SMA
        sma_slow = SMA(feeder, 75)          # 長期SMA
        rsi_fast = RSI(feeder, 7)
        rsi_slow = RSI(feeder, 13)

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.indicators_left.append(sma_fast)
        window_main.indicators_left.append(sma_middle)
        window_main.indicators_left.append(sma_slow)

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.append(rsi_fast)
        window_sub.indicators_left.append(rsi_slow)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        # on_tickイベントに受け渡すデータを格納する
        data_bag["sma_fast"] = sma_fast
        data_bag["sma_middle"] = sma_middle
        data_bag["sma_slow"] = sma_slow
        data_bag["rsi_fast"] = rsi_fast
        data_bag["rsi_slow"] = rsi_slow

    def _on_tick(self, candle: Candle, data_bag: dict, position_repository: PositionRepository):
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
        """

        # 受け渡されたデータを引き出す
        sma_fast = data_bag["sma_fast"]
        sma_middle = data_bag["sma_middle"]
        sma_slow = data_bag["sma_slow"]
        rsi_fast = data_bag["rsi_fast"]
        rsi_slow = data_bag["rsi_slow"]

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


if __name__ == "__main__":

    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "5m", "forwardtest")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "5m", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))

    mytrade.run()
