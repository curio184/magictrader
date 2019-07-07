import time
from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart
from magictrader.const import APPLIED_PRICE, MODE_BBANDS, MODE_MACD
from magictrader.indicator import ADX, BBANDS, MACD, RSI, SMA, STDDEV


if __name__ == "__main__":

    # feeder = CandleFeeder("btc_jpy", "5m")
    feeder = CandleFeeder("btc_jpy", "5m", True, datetime(2019, 3, 1), datetime(2019, 6, 30))
    chart = None

    while True:

        candle = Candle(feeder, 200)
        sma_fast = SMA(feeder, 200, 21, APPLIED_PRICE.CLOSE)
        sma_middle = SMA(feeder, 200, 89, APPLIED_PRICE.CLOSE)
        sma_slow = SMA(feeder, 200, 200, APPLIED_PRICE.CLOSE)
        bb_u1 = BBANDS(feeder, 200, 20, 1, MODE_BBANDS.UPPER, APPLIED_PRICE.CLOSE)
        bb_l1 = BBANDS(feeder, 200, 20, 1, MODE_BBANDS.LOWER, APPLIED_PRICE.CLOSE)
        stddev = STDDEV(feeder, 200, 20, 1, APPLIED_PRICE.CLOSE)
        macd_fast = MACD(feeder, 200, 12, 26, 9, MODE_MACD.FAST, APPLIED_PRICE.CLOSE)
        macd_slow = MACD(feeder, 200, 12, 26, 9, MODE_MACD.SLOW, APPLIED_PRICE.CLOSE)
        macd_signal = MACD(feeder, 200, 12, 26, 9, MODE_MACD.SIGNAL, APPLIED_PRICE.CLOSE)
        adx = ADX(feeder, 200, 20)
        rsi = RSI(feeder, 200, 20, APPLIED_PRICE.CLOSE)

        if chart:
            chart.update("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])
        else:
            chart = Chart("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])

        feeder.go_next()
        time.sleep(0.01)
