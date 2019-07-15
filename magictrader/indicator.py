from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

import talib

from magictrader.candle import CandleFeeder
from magictrader.const import (AppliedPrice, ModeBBANDS, ModeMACD,
                               ModeTRADESIGNAL)
from magictrader.event import EventArgs


class Indicator(metaclass=ABCMeta):
    """
    テクニカルインディケーターを表します。
    """

    def __init__(self, feeder: CandleFeeder, label: str):
        self._feeder = feeder
        self._feeder.ohlc_updated_eventhandler.add(self._ohlc_updated)
        self._times = []
        self._prices = []
        self._label = label
        self._style = {}
        self._apply_default_style()
        self._load()

    def _apply_default_style(self):
        """
        既定のスタイルを適用します。
        """
        self._style = {"linestyle": "solid", "color": "gray", "linewidth": 1, "alpha": 1}

    @abstractmethod
    def _load(self):
        """
        テクニカルインディケーターを読み込みます。
        """
        pass

    def refresh(self):
        """
        テクニカルインディケーターを再読み込みします。
        """
        self._load()

    def _ohlc_updated(self, sender: object, eargs: EventArgs):
        """
        ローソク足が更新されたときに発生します。
        """
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


class TRADESIGNAL(Indicator):
    """
    売買シグナル
    """

    def __init__(self, feeder: CandleFeeder, mode_tradesignal: ModeTRADESIGNAL, label: str = None):
        self._mode_tradesignal = mode_tradesignal
        if label is None:
            if self._mode_tradesignal == ModeTRADESIGNAL.BUY_OPEN:
                label = "buy open"
            elif self._mode_tradesignal == ModeTRADESIGNAL.BUY_CLOSE:
                label = "buy close"
            elif self._mode_tradesignal == ModeTRADESIGNAL.SELL_OPEN:
                label = "sell open"
            elif self._mode_tradesignal == ModeTRADESIGNAL.SELL_CLOSE:
                label = "sell close"
        super().__init__(feeder, label)

    def _apply_default_style(self):
        if self._mode_tradesignal == ModeTRADESIGNAL.BUY_OPEN:
            self.style = {"marker": "^", "color": "red", "ms": 10}
        elif self._mode_tradesignal == ModeTRADESIGNAL.BUY_CLOSE:
            self.style = {"marker": "v", "color": "blue", "ms": 10}
        elif self._mode_tradesignal == ModeTRADESIGNAL.SELL_OPEN:
            self.style = {"marker": "v", "color": "green", "ms": 10}
        elif self._mode_tradesignal == ModeTRADESIGNAL.SELL_CLOSE:
            self.style = {"marker": "^", "color": "purple", "ms": 10}
        else:
            super()._apply_default_style()

    def _load(self):
        prev_times = self._times
        prev_prices = self._prices

        self._times = self._feeder.get_times()
        self._prices = [None] * self._feeder.bar_count

        for cur_idx, cur_time in enumerate(self._times):
            for prev_idx, prev_time in enumerate(prev_times):
                if prev_time == cur_time:
                    self.prices[cur_idx] = prev_prices[prev_idx]


class SMA(Indicator):
    """
    単純移動平均を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "sma",
                 applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        if 1 <= self._period <= 12:
            self.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        elif 13 <= self._period <= 74:
            self.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}
        elif 75 <= self._period <= 200:
            self.style = {"linestyle": "solid", "color": "blue", "linewidth": 1, "alpha": 1}
        else:
            super()._apply_default_style()

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class BBANDS(Indicator):
    """
    ボリンジャーバンドを表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, deviation: int, mode_bbands: ModeBBANDS,
                 label: str = "bbands", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._deviation = deviation
        self._mode_bbands = mode_bbands
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "solid", "color": "magenta", "linewidth": 1, "alpha": 0.1}

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
    """
    標準偏差を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, deviation: int,
                 label: str = "stddev", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "solid", "color": "purple", "linewidth": 1, "alpha": 1}

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.STDDEV(prices, timeperiod=self._period, nbdev=self._deviation)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class MACD(Indicator):
    """
    MACDを表します。
    """

    def __init__(self, feeder: CandleFeeder, fast_period: int, slow_period: int, signal_period, mode_macd: ModeMACD,
                 label: str = "macd", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        self._mode_macd = mode_macd
        self._applied_price = applied_price
        super().__init__(feeder, label)

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
    """
    ADXを表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "adx"):
        self._period = period
        super().__init__(feeder, label)

    def _load(self):
        self._times = self._feeder.get_times()
        # NOTE:仮実装
        highs = self._feeder.get_prices(25, AppliedPrice.HIGH)
        lows = self._feeder.get_prices(25, AppliedPrice.LOW)
        closes = self._feeder.get_prices(25, AppliedPrice.CLOSE)
        prices = talib.ADX(high=highs, low=lows, close=closes, timeperiod=self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class RSI(Indicator):
    """
    RSIを表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "rsi",
                 applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.RSI(prices, timeperiod=self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class ENVELOPE(Indicator):
    """
    エンベロープを表します。
    """
    # NOTE:仮実装

    def __init__(self, feeder: CandleFeeder, period: int, deviation: float,
                 label: str = "envelope", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        prices = prices * self._deviation
        self._prices = prices[-self._feeder.bar_count:].tolist()
