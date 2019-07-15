from datetime import datetime

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import AppliedPrice, ModeBBANDS, ModeMACD
from magictrader.indicator import ADX, BBANDS, MACD, RSI, SMA, STDDEV
from magictrader.terminal import TradeTerminal
from magictrader.trade import Position, PositionRepository


class MyTerminal(TradeTerminal):

    def _on_init(self, feeder: CandleFeeder, chart: Chart, window_main: ChartWindow, data_bag: dict):

        # テクニカルインディケーターを作成する
        sma_fast = SMA(feeder, 21)
        sma_slow = SMA(feeder, 89)
        adx_fast = ADX(feeder, 13)
        adx_slow = ADX(feeder, 26)
        stddev = STDDEV(feeder, 20, 1)

        # チャート(メイン画面)にインディケーターを登録する
        window_main.indicators_left.append(sma_fast)      # 短期SMAを設定
        window_main.indicators_left.append(sma_slow)      # 長期SMAを設定

        # チャート(サブ画面)を作成し、インディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.append(adx_fast)
        window_sub.indicators_left.append(adx_slow)
        window_sub.indicators_right.append(stddev)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        data_bag["sma_fast"] = sma_fast
        data_bag["sma_slow"] = sma_slow
        data_bag["adx_fast"] = adx_fast
        data_bag["sma_fast"] = sma_fast
        data_bag["adx_slow"] = adx_slow
        data_bag["stddev"] = stddev

    def _on_tick(self, candle: Candle, data_bag: dict, position_repository: PositionRepository):

        sma_fast = data_bag["sma_fast"]
        sma_slow = data_bag["sma_slow"]
        adx_fast = data_bag["adx_fast"]
        sma_fast = data_bag["sma_fast"]
        adx_slow = data_bag["adx_slow"]
        stddev = data_bag["stddev"]

        if sma_fast.prices[-3] < sma_slow.prices[-3]  \
                and sma_fast.prices[-2] > sma_slow.prices[-2]:

            position = position_repository.create_position()
            position.open(self._candle.times[-1], "buy", self._candle.closes[-1], 1, "")


if __name__ == "__main__":

    terminal = MyTerminal("btc_jpy", "5m", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))
    terminal.run()
