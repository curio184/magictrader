from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

import talib
from pyti import stochastic

from magictrader.candle import CandleFeeder
from magictrader.const import AppliedPrice, ModeBAND, ModeMACD, ModeTRADESIGNAL
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


class HLine(Indicator):
    """
    水平線を表します。
    """

    def __init__(self, feeder: CandleFeeder, price: float, label: str = "hline"):
        self._price = price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "dotted", "color": "red", "linewidth": 1, "alpha": 1}

    def _load(self):
        self._times = self._feeder.get_times()
        self._prices = [self._price] * self._feeder.bar_count


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


class EMA(Indicator):
    """
    指数平滑移動平均を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "ema",
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
        prices = talib.EMA(prices, self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class WMA(Indicator):
    """
    加重移動平均を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "ema",
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
        prices = talib.WMA(prices, self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class ENVELOPE(Indicator):
    """
    エンベロープを表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, deviation: float,
                 label: str = "envelope", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._deviation = deviation
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "dashdot", "color": "grey", "linewidth": 0.5, "alpha": 1}

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.SMA(prices, self._period)
        prices = prices + (prices * self._deviation)
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

    def _apply_default_style(self):
        if self._mode_macd == ModeMACD.MACD:
            self.style = {"linestyle": "solid", "color": "blue", "linewidth": 1, "alpha": 1}
        elif self._mode_macd == ModeMACD.SIGNAL:
            self.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
            self.label = "macd_signal"
        else:
            super()._apply_default_style()
            self.label = "macd_histogram"

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._slow_period + self._signal_period, self._applied_price)
        macd = talib.EMA(prices, self._fast_period) - talib.EMA(prices, self._slow_period)
        macd_signal = talib.EMA(macd, self._signal_period)
        macd_histogram = macd - macd_signal
        if self._mode_macd == ModeMACD.MACD:
            self._prices = macd[-self._feeder.bar_count:].tolist()
        elif self._mode_macd == ModeMACD.SIGNAL:
            self._prices = macd_signal[-self._feeder.bar_count:].tolist()
        elif self._mode_macd == ModeMACD.HISTOGRAM:
            self._prices = macd_histogram[-self._feeder.bar_count:].tolist()


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


class BBANDS(Indicator):
    """
    ボリンジャーバンドを表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, deviation: int, mode_bbands: ModeBAND,
                 label: str = "bbands", applied_price: AppliedPrice = AppliedPrice.CLOSE):
        self._period = period
        self._deviation = deviation
        self._mode_band = mode_bbands
        self._applied_price = applied_price
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "solid", "color": "magenta", "linewidth": 1, "alpha": 0.1}

    def _load(self):
        self._times = self._feeder.get_times()
        prices = self._feeder.get_prices(self._period, self._applied_price)
        prices = talib.BBANDS(prices, timeperiod=self._period, nbdevup=self._deviation, nbdevdn=self._deviation, matype=0)
        if self._mode_band == ModeBAND.UPPER:
            self._prices = prices[0][-self._feeder.bar_count:].tolist()
        elif self._mode_band == ModeBAND.MIDDLE:
            self._prices = prices[1][-self._feeder.bar_count:].tolist()
        elif self._mode_band == ModeBAND.LOWER:
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


class ADX(Indicator):
    """
    ADX(修正移動平均)を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "adx"):
        self._period = period
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
        highs = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.HIGH)
        lows = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.LOW)
        closes = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.CLOSE)
        prices = talib.ADX(high=highs, low=lows, close=closes, timeperiod=self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class ATR(Indicator):
    """
    ATR(Average True Range)を表します。
    """

    def __init__(self, feeder: CandleFeeder, period: int, label: str = "atr"):
        self._period = period
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
        highs = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.HIGH)
        lows = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.LOW)
        closes = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.CLOSE)
        prices = talib.ATR(highs, lows, closes, self._period)
        self._prices = prices[-self._feeder.bar_count:].tolist()


class ATRBAND(Indicator):
    """
    ATRBAND(Average True Range Band)を表します。
    """

    def __init__(self, feeder: CandleFeeder, wma_period: int, atr_period: int,
                 deviation: int, mode_band: ModeBAND, label: str = "atr_band"):
        self._wma_period = wma_period
        self._atr_period = atr_period
        self._deviation = deviation
        self._mode_band = mode_band
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "solid", "color": "magenta", "linewidth": 1, "alpha": 0.3}

    def _load(self):
        self._times = self._feeder.get_times()
        # WMA
        closes = self._feeder.get_prices(self._wma_period, AppliedPrice.CLOSE)
        prices_wma = talib.WMA(closes, self._wma_period)
        prices_wma = prices_wma[-self._feeder.bar_count:]
        # ATR
        highs = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.HIGH)
        lows = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.LOW)
        closes = self._feeder.get_prices(self._feeder.bar_count, AppliedPrice.CLOSE)
        prices_atr = talib.ATR(highs, lows, closes, self._atr_period)
        prices_atr = prices_atr[-self._feeder.bar_count:] * self._deviation * 1.6
        # BAND
        if self._mode_band == ModeBAND.UPPER:
            self._prices = (prices_wma + prices_atr).tolist()
        elif self._mode_band == ModeBAND.MIDDLE:
            self._prices = prices_wma.tolist()
        elif self._mode_band == ModeBAND.LOWER:
            self._prices = (prices_wma - prices_atr).tolist()


class SchaffTC(Indicator):
    """
    Schaff Trend Cycleを表します。
    """

    def __init__(self, feeder: CandleFeeder,  label: str = "schaff_tc"):
        super().__init__(feeder, label)

    def _apply_default_style(self):
        self.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}

    def _load(self):
        self._times = self._feeder.get_times()

        # Default Params
        ma_fast_period = 23     # MACD Fast Length
        ma_slow_period = 50     # MACD Slow Length
        cycle_length = 10       # Cycle Length
        d1_length = 3           # 1st %D Length
        d2_length = 3           # 2nd %D Length

        # close
        prices_close = self._feeder.get_prices(200, AppliedPrice.CLOSE)

        # macd
        ema_fast = talib.EMA(prices_close, ma_fast_period)
        ema_slow = talib.EMA(prices_close, ma_slow_period)
        macd = ema_fast - ema_slow

        # stocastic from the macd
        k1 = stochastic.percent_k(macd, cycle_length)
        d1 = talib.EMA(k1, d1_length)

        # stocastic from the macd
        k2 = stochastic.percent_k(d1, cycle_length)
        d2 = talib.EMA(k2, d2_length)

        self._prices = d2[-self._feeder.bar_count:].tolist()
