from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import AppliedPrice, ModeBBANDS, ModeMACD
from magictrader.indicator import (ADX, BBANDS, MACD, RSI, SMA, STDDEV,
                                   Indicator)

if __name__ == "__main__":

    feeder = CandleFeeder("btc_jpy", "5m", 200, True, datetime(2019, 3, 1), datetime(2019, 6, 30))
    # feeder = CandleFeeder("btc_jpy", "5m", 200)

    candle = Candle(feeder)
    sma_fast = SMA(feeder, 21, AppliedPrice.CLOSE)
    sma_slow = SMA(feeder, 89, AppliedPrice.CLOSE)

    adx_fast = ADX(feeder, 13)
    adx_slow = ADX(feeder, 26)
    stddev = STDDEV(feeder, 20, 1, AppliedPrice.CLOSE)

    window_main = ChartWindow()
    window_main.title = "btc_jpy"
    window_main.height_ratio = 3
    window_main.candle = candle
    window_main.indicators_left.append(sma_fast)
    window_main.indicators_left.append(sma_slow)

    window_sub = ChartWindow()
    window_sub.height_ratio = 1
    window_sub.ylabel_left = "adx"
    window_sub.ylabel_right = "stddev"
    window_sub.legend_visible = True
    window_sub.indicators_left.append(adx_fast)
    window_sub.indicators_left.append(adx_slow)
    window_sub.indicators_right.append(stddev)

    chart = Chart()
    chart.add_window(window_main)
    chart.add_window(window_sub)
    chart.show()

    while True:

        feeder.go_next()
        chart.refresh()

        # # 日時を描画
        # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
        # self._fig.autofmt_xdate()
        # # 日時を描画
        # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
        # self._fig.autofmt_xdate()
