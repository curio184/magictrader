import time
from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart
from magictrader.const import AppliedPrice, ModeBBANDS, ModeMACD
from magictrader.indicator import ADX, BBANDS, MACD, RSI, SMA, STDDEV


class TradeTerminal:

    def __init__(self, currency_pair: str, period: str, trade_mode: str, datetime_from: datetime, datetime_to: datetime):

        self._currency_pair = currency_pair
        self._period = period
        self._trade_mode = trade_mode
        self._datetime_from = datetime_from
        self._datetime_to = datetime_to

        self._chart = None
        self._feeder = None
        if self._trade_mode == "practice":
            self._feeder = CandleFeeder(self._currency_pair, self._period, 200)
        elif self._trade_mode == "backtest":
            self._feeder = CandleFeeder(self._currency_pair, self._period, 200, True, datetime(2019, 3, 1), datetime(2019, 6, 30))
        elif self._trade_mode == "forwardtest":
            self._feeder = CandleFeeder(self._currency_pair, self._period, 200, True, datetime(2019, 3, 1), datetime(2019, 6, 30))

    def start(self):

        while True:
            self.on_tick()
            self._feeder.go_next()

    def on_start(self):
        pass

    def on_tick(self):

        candle = Candle(self._feeder)
        sma_fast = SMA(self._feeder, 21, AppliedPrice.CLOSE)
        sma_middle = SMA(self._feeder, 89, AppliedPrice.CLOSE)
        sma_slow = SMA(self._feeder, 200, AppliedPrice.CLOSE)
        bb_u1 = BBANDS(self._feeder, 20, 1, ModeBBANDS.UPPER, AppliedPrice.CLOSE)
        bb_l1 = BBANDS(self._feeder, 20, 1, ModeBBANDS.LOWER, AppliedPrice.CLOSE)
        stddev = STDDEV(self._feeder, 20, 1, AppliedPrice.CLOSE)
        macd_fast = MACD(self._feeder, 12, 26, 9, ModeMACD.FAST, AppliedPrice.CLOSE)
        macd_slow = MACD(self._feeder, 12, 26, 9, ModeMACD.SLOW, AppliedPrice.CLOSE)
        macd_signal = MACD(self._feeder, 12, 26, 9, ModeMACD.SIGNAL, AppliedPrice.CLOSE)
        adx = ADX(self._feeder, 20)
        rsi = RSI(self._feeder, 20, AppliedPrice.CLOSE)

        if self._chart:
            self._chart.update("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])
        else:
            self._chart = Chart("title", candle, [sma_fast, sma_middle, sma_slow, bb_u1, bb_l1], [([stddev, adx, rsi], [macd_fast, macd_slow, macd_signal])])


if __name__ == "__main__":

    terminal = TradeTerminal("btc_jpy", "5m", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))
    terminal.start()
