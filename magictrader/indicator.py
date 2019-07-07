from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

import numpy
import talib

from magictrader.candle import CandleFeeder
from magictrader.const import APPLIED_PRICE, MODE_BBANDS, MODE_MACD


class Indicator(metaclass=ABCMeta):

    def __init__(self, feeder: CandleFeeder, label: str, bar_count: int):
        self._feeder = feeder
        self._bar_count = bar_count
        self._times = []
        self._prices = []
        self._label = label
        self._style = {"linestyle": "solid", "color": "gray", "linewidth": 1, "alpha": 1}
        self._load()

    @abstractmethod
    def _load(self):
        pass

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

    def __init__(self, feeder: CandleFeeder, bar_count: int, period: int, applied_price: APPLIED_PRICE):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, "sma", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        prices = self._feeder.get_prices(self._bar_count + self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        self._prices = prices[-self._bar_count:].tolist()


class BBANDS(Indicator):

    def __init__(self, feeder: CandleFeeder, bar_count: int, period: int, deviation: int, mode_bbands: MODE_BBANDS, applied_price: APPLIED_PRICE):
        self._period = period
        self._deviation = deviation
        self._mode_bbands = mode_bbands
        self._applied_price = applied_price
        super().__init__(feeder, "bbands", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        prices = self._feeder.get_prices(self._bar_count + self._period, self._applied_price)
        prices = talib.BBANDS(prices, timeperiod=self._period, nbdevup=self._deviation, nbdevdn=self._deviation, matype=0)
        if self._mode_bbands == MODE_BBANDS.UPPER:
            self._prices = prices[0][-self._bar_count:].tolist()
        elif self._mode_bbands == MODE_BBANDS.MIDDLE:
            self._prices = prices[1][-self._bar_count:].tolist()
        elif self._mode_bbands == MODE_BBANDS.LOWER:
            self._prices = prices[2][-self._bar_count:].tolist()


class STDDEV(Indicator):

    def __init__(self, feeder: CandleFeeder, bar_count: int, period: int, deviation: int, applied_price: APPLIED_PRICE):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, "stddev", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        prices = self._feeder.get_prices(self._bar_count + self._period, self._applied_price)
        prices = talib.STDDEV(prices, timeperiod=self._period, nbdev=self._deviation)
        self._prices = prices[-self._bar_count:].tolist()


class MACD(Indicator):

    def __init__(self, feeder: CandleFeeder, bar_count: int, fast_period: int, slow_period: int, signal_period, mode_macd: MODE_MACD, applied_price: APPLIED_PRICE):
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        self._mode_macd = mode_macd
        self._applied_price = applied_price
        super().__init__(feeder, "macd", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        prices = self._feeder.get_prices(self._bar_count + self._slow_period, self._applied_price)
        prices = talib.MACD(prices, fastperiod=self._fast_period, slowperiod=self._slow_period, signalperiod=self._signal_period)
        if self._mode_macd == MODE_MACD.FAST:
            self._prices = prices[0][-self._bar_count:].tolist()
        elif self._mode_macd == MODE_MACD.SLOW:
            self._prices = prices[1][-self._bar_count:].tolist()
        elif self._mode_macd == MODE_MACD.SIGNAL:
            self._prices = prices[2][-self._bar_count:].tolist()


class ADX(Indicator):

    def __init__(self, feeder: CandleFeeder, bar_count: int, period: int):
        self._period = period
        super().__init__(feeder, "adx", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        highs = self._feeder.get_prices(self._bar_count + self._period, APPLIED_PRICE.HIGH)
        lows = self._feeder.get_prices(self._bar_count + self._period, APPLIED_PRICE.LOW)
        closes = self._feeder.get_prices(self._bar_count + self._period, APPLIED_PRICE.CLOSE)
        prices = talib.ADX(high=highs, low=lows, close=closes, timeperiod=self._period)
        self._prices = prices[-self._bar_count:].tolist()


class RSI(Indicator):

    def __init__(self, feeder: CandleFeeder, bar_count: int, period: int, applied_price: APPLIED_PRICE):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, "rsi", bar_count)

    def _load(self):
        self._times = self._feeder.get_times(self._bar_count)
        prices = self._feeder.get_prices(self._bar_count + self._period, self._applied_price)
        prices = talib.RSI(prices, timeperiod=self._period)
        self._prices = prices[-self._bar_count:].tolist()
