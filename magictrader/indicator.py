from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

import talib

from magictrader.candle import CandleFeeder
from magictrader.const import AppliedPrice, ModeBBANDS, ModeMACD


class Indicator(metaclass=ABCMeta):

    def __init__(self, feeder: CandleFeeder, label: str):
        self._feeder = feeder
        self._times = []
        self._prices = []
        self._label = label
        self._style = {"linestyle": "solid", "color": "gray", "linewidth": 1, "alpha": 1}
        self._load()

    @abstractmethod
    def _load(self):
        pass

    def refresh(self):
        self._load()

    @property
    def times(self) -> List[datetime]:
        return self._times

    @property
    def prices(self) -> List[float]:
        return self._prices

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value

    @property
    def style(self) -> dict:
        return self._style

    @style.setter
    def style(self, value: dict):
        # {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        # {"linestyle": "solid", "color": "blue", "linewidth": 1, "alpha": 1}
        # {"marker": "^", "color": "red", "ms": 10}
        # {"marker": "^", "color": "blue", "ms": 10}
        self._style = value


class SMA(Indicator):

    def __init__(self, feeder: CandleFeeder, period: int, applied_price: AppliedPrice):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, "sma")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class BBANDS(Indicator):

    def __init__(self, feeder: CandleFeeder, period: int, deviation: int, mode_bbands: ModeBBANDS, applied_price: AppliedPrice):
        self._period = period
        self._deviation = deviation
        self._mode_bbands = mode_bbands
        self._applied_price = applied_price
        super().__init__(feeder, "bbands")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.BBANDS(prices, timeperiod=self._period, nbdevup=self._deviation, nbdevdn=self._deviation, matype=0)
        if self._mode_bbands == ModeBBANDS.UPPER:
            self._prices = prices[0][-self._feeder.bar_count:].tolist()
        elif self._mode_bbands == ModeBBANDS.MIDDLE:
            self._prices = prices[1][-self._feeder.bar_count:].tolist()
        elif self._mode_bbands == ModeBBANDS.LOWER:
            self._prices = prices[2][-self._feeder.bar_count:].tolist()


class STDDEV(Indicator):

    def __init__(self, feeder: CandleFeeder, period: int, deviation: int, applied_price: AppliedPrice):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, "stddev")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.STDDEV(prices, timeperiod=self._period, nbdev=self._deviation)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class MACD(Indicator):

    def __init__(self, feeder: CandleFeeder, fast_period: int, slow_period: int, signal_period, mode_macd: ModeMACD, applied_price: AppliedPrice):
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        self._mode_macd = mode_macd
        self._applied_price = applied_price
        super().__init__(feeder, "macd")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._slow_period, self._applied_price)
        prices = talib.MACD(prices, fastperiod=self._fast_period, slowperiod=self._slow_period, signalperiod=self._signal_period)
        if self._mode_macd == ModeMACD.FAST:
            self._prices = prices[0][-self._feeder.bar_count:].tolist()
        elif self._mode_macd == ModeMACD.SLOW:
            self._prices = prices[1][-self._feeder.bar_count:].tolist()
        elif self._mode_macd == ModeMACD.SIGNAL:
            self._prices = prices[2][-self._feeder.bar_count:].tolist()


class ADX(Indicator):
    # 仮実装(25を定数として使っている)

    def __init__(self, feeder: CandleFeeder, period: int):
        self._period = period
        super().__init__(feeder, "adx")

    def _load(self):
        self._times = self._feeder.get_times()
        highs = self._feeder.get_prices(25, AppliedPrice.HIGH)
        lows = self._feeder.get_prices(25, AppliedPrice.LOW)
        closes = self._feeder.get_prices(25, AppliedPrice.CLOSE)
        prices = talib.ADX(high=highs, low=lows, close=closes, timeperiod=self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class RSI(Indicator):

    def __init__(self, feeder: CandleFeeder, period: int, applied_price: AppliedPrice):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, "rsi")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.RSI(prices, timeperiod=self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class ENVELOPE(Indicator):
    # NOTE:仮実装

    def __init__(self, feeder: CandleFeeder, period: int, deviation: float, applied_price: AppliedPrice):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, "envelope")

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        prices = prices * self._deviation
        self._prices = prices[-self._feeder.bar_count:].tolist()


class SIGNAL(Indicator):
    # NOTE:仮実装

    def __init__(self, feeder: CandleFeeder, prev=None):
        self._prev = prev
        super().__init__(feeder, "signal")

    def _load(self):
        self._times = self._feeder.get_times()
        self._prices = [None] * self._feeder.bar_count
        if self._prev:
            for idx_p, time_p in enumerate(self._prev.times):
                if self._prev.prices[idx_p]:
                    for idx_c, time_c in enumerate(self._times):
                        if time_p == time_c:
                            self._prices[idx_c] = self._prev.prices[idx_p]
            self.label = self._prev.label
            self.style = self._prev.style
