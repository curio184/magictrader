from datetime import datetime, timedelta
from typing import List

import numpy
from sqlalchemy import asc
from zaifer import Chart as ChartAPI

from magictrader.const import APPLIED_PRICE, Period
from magictrader.model import CandleOHLC, DBContext
from magictrader.utils import TimeConverter


class CandleFeeder:

    def __init__(self, currency_pair: str, period: str, is_backtest: bool = False, datetime_from: datetime = None, datetime_to: datetime = None):
        self._currency_pair = currency_pair
        self._period = period
        self._cache_bar_count = 1000
        self._is_backtest = is_backtest
        # バックテストの場合
        if self._is_backtest:
            self._datetime_cursor = datetime_from
            self._datetime_from = datetime_from
            self._datetime_to = datetime_to
        # フォワードテストの場合
        else:
            self._datetime_cursor = datetime.now()
            self._datetime_from = self._datetime_cursor
            self._datetime_to = self._datetime_cursor
        self._db_context = DBContext()
        self._chart_api = ChartAPI()
        self._ohlcs = {}
        self.go_next()

        self._server_request_span = 5
        self._server_request_latest = None
        self._cache_bar_max_time = None

    def get_ohlcs(self, bar_count: int) -> dict:
        return {
            "times": self.get_times(bar_count),
            "opens": self.get_prices(bar_count, APPLIED_PRICE.OPEN),
            "highs": self.get_prices(bar_count, APPLIED_PRICE.HIGH),
            "lows": self.get_prices(bar_count, APPLIED_PRICE.LOW),
            "closes": self.get_prices(bar_count, APPLIED_PRICE.CLOSE),
        }

    def get_times(self, bar_count: int) -> List[datetime]:
        return self._ohlcs["times"][self._cache_bar_count-bar_count:self._cache_bar_count]

    def get_prices(self, bar_count: int, applied_price: APPLIED_PRICE) -> numpy.ndarray:
        if applied_price == APPLIED_PRICE.OPEN:
            return self._ohlcs["opens"][self._cache_bar_count-bar_count:self._cache_bar_count]
        elif applied_price == APPLIED_PRICE.HIGH:
            return self._ohlcs["highs"][self._cache_bar_count-bar_count:self._cache_bar_count]
        elif applied_price == APPLIED_PRICE.LOW:
            return self._ohlcs["lows"][self._cache_bar_count-bar_count:self._cache_bar_count]
        elif applied_price == APPLIED_PRICE.CLOSE:
            return self._ohlcs["closes"][self._cache_bar_count-bar_count:self._cache_bar_count]

    def go_next(self) -> bool:

        # バックテストの場合
        if self._is_backtest:

            if self._datetime_cursor < self._datetime_to:

                # ローソク足の取得範囲を計算する
                self._datetime_cursor += timedelta(minutes=5)
                range_from = self._datetime_cursor - timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
                range_to = self._datetime_cursor

                # キャッシュからローソク足を取得する
                ohlcs = self._get_ohlcs_from_local(range_from, range_to)

                # キャッシュがヒットしなかった場合
                if len(ohlcs["times"]) != self._cache_bar_count:

                    # サーバーからローソク足を取得する
                    extra_range_from = range_from
                    extra_range_to = range_to + timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
                    ohlcs = self._get_ohlcs_from_server(extra_range_from, extra_range_to)

                    # キャッシュにローソク足を保存する
                    self._save_ohlcs_to_local(ohlcs)

                    # キャッシュからローソク足を取得する
                    ohlcs = self._get_ohlcs_from_local(range_from, range_to)

                self._ohlcs = ohlcs

                return True

            else:

                return False

        # フォワードテストの場合
        else:

            # ローソク足の取得範囲を計算する
            self._cursor_datetime = datetime.now()
            self._to_datetime = self._cursor_datetime
            range_from = self._cursor_datetime - timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
            range_to = self._cursor_datetime

            # サーバーからローソク足を取得する
            self._ohlcs = self._get_ohlcs_from_server(range_from, range_to)

            return True

    def _get_ohlcs_from_local(self, range_from: datetime, range_to: datetime) -> dict:
        """
        ローカルからローソク足を取得する
        """

        records = self._db_context.session.query(CandleOHLC) \
            .filter(CandleOHLC.currency_pair == self._currency_pair) \
            .filter(CandleOHLC.period == self._period) \
            .filter(CandleOHLC.time >= range_from) \
            .filter(CandleOHLC.time <= range_to) \
            .order_by(asc(CandleOHLC.time)) \
            .all()

        return {
            "times": list(map(lambda x: x.time, records)),
            "opens": numpy.array(list(map(lambda x: float(str(x.open)), records))),
            "highs": numpy.array(list(map(lambda x: float(str(x.high)), records))),
            "lows": numpy.array(list(map(lambda x: float(str(x.low)), records))),
            "closes": numpy.array(list(map(lambda x: float(str(x.close)), records))),
        }

    def _save_ohlcs_to_local(self, ohlcs: dict):
        """
        ローカルにローソク足を保存する
        """

        # ローカルにデータを保存する
        for idx, item in enumerate(ohlcs["times"]):

            # ローカルをUPSERTする
            record = self._db_context.session.query(CandleOHLC) \
                .filter(CandleOHLC.currency_pair == self._currency_pair) \
                .filter(CandleOHLC.period == self._period) \
                .filter(CandleOHLC.time == item) \
                .first()

            if record:
                record.open = ohlcs["opens"][idx]
                record.high = ohlcs["highs"][idx]
                record.low = ohlcs["lows"][idx]
                record.close = ohlcs["closes"][idx]
            else:
                record = CandleOHLC(
                    currency_pair=self._currency_pair,
                    period=self._period,
                    time=ohlcs["times"][idx],
                    open=ohlcs["opens"][idx],
                    high=ohlcs["highs"][idx],
                    low=ohlcs["lows"][idx],
                    close=ohlcs["closes"][idx]
                )
                self._db_context.session.add(record)

        self._db_context.session.flush()
        self._db_context.session.commit()

    def _get_ohlcs_from_server(self, range_from: datetime, range_to: datetime) -> dict:
        """
        サーバーからローソク足を取得する
        """

        response = self._chart_api.get_ohlc(self._currency_pair, Period.to_str_for_zaifapi(self._period), range_from, range_to)
        return {
            "times": list(map(lambda x: TimeConverter.unixtime_to_datetime(int(x["time"]/1000)), response["ohlc_data"])),
            "opens": numpy.array(list(map(lambda x: x["open"], response["ohlc_data"]))),
            "highs": numpy.array(list(map(lambda x: x["high"], response["ohlc_data"]))),
            "lows": numpy.array(list(map(lambda x: x["low"], response["ohlc_data"]))),
            "closes": numpy.array(list(map(lambda x: x["close"], response["ohlc_data"]))),
        }

    @property
    def is_backtest(self) -> bool:
        return self._is_backtest

    @property
    def datetime_from(self) -> datetime:
        return self._datetime_from

    @property
    def datetime_to(self) -> datetime:
        return self._datetime_to

    @property
    def datetime_cursor(self) -> datetime:
        return self._datetime_cursor


class Candle:
    """
    ローソク足を表すクラス
    """

    def __init__(self, feeder: CandleFeeder, bar_count: int,):
        candles = feeder.get_ohlcs(bar_count)
        self._times = candles["times"]
        self._opens = candles["opens"].tolist()
        self._closes = candles["closes"].tolist()
        self._lows = candles["lows"].tolist()
        self._highs = candles["highs"].tolist()

    @property
    def times(self) -> List[datetime]:
        return self._times

    @property
    def opens(self) -> List[float]:
        return self._opens

    @property
    def closes(self) -> List[float]:
        return self._closes

    @property
    def lows(self) -> List[float]:
        return self._lows

    @property
    def highs(self) -> List[float]:
        return self._highs

    @property
    def width(self) -> float:
        return 0.8
