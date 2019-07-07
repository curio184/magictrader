import time
from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart
from magictrader.const import AppliedPrice, ModeBBANDS, ModeMACD
from magictrader.indicator import ADX, BBANDS, MACD, RSI, SMA, STDDEV

if __name__ == "__main__":

    # feeder = CandleFeeder("btc_jpy", "5m", 200)
    feeder = CandleFeeder("btc_jpy", "5m", 200, True, datetime(2019, 3, 1), datetime(2019, 6, 30))
    chart = None

    while True:

        candle = Candle(feeder)
        sma_fast = SMA(feeder, 21, AppliedPrice.CLOSE)
        sma_middle = SMA(feeder, 89, AppliedPrice.CLOSE)
        sma_slow = SMA(feeder, 200, AppliedPrice.CLOSE)
        bb_u1 = BBANDS(feeder, 20, 1, ModeBBANDS.UPPER, AppliedPrice.CLOSE)
        bb_l1 = BBANDS(feeder, 20, 1, ModeBBANDS.LOWER, AppliedPrice.CLOSE)
        stddev = STDDEV(feeder, 20, 1, AppliedPrice.CLOSE)
        macd_fast = MACD(feeder, 12, 26, 9, ModeMACD.FAST, AppliedPrice.CLOSE)
        macd_slow = MACD(feeder, 12, 26, 9, ModeMACD.SLOW, AppliedPrice.CLOSE)
        macd_signal = MACD(feeder, 12, 26, 9, ModeMACD.SIGNAL, AppliedPrice.CLOSE)
        adx = ADX(feeder, 20)
        rsi = RSI(feeder, 20, AppliedPrice.CLOSE)

        if chart:
            chart.update("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])
        else:
            chart = Chart("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])

        feeder.go_next()
        time.sleep(0.01)
