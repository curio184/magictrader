import time
from datetime import datetime, timedelta
from typing import List

import numpy
from sqlalchemy import asc
from zaifer import Chart as ChartAPI

from magictrader.const import AppliedPrice, Period
from magictrader.event import EventArgs, EventHandler
from magictrader.model import CandleOHLC, DBContext
from magictrader.utils import TimeConverter


class CandleFeeder:
    """
    ローソク足を供給します。
    """

    def __init__(self, currency_pair: str, period: str, bar_count: int, backtest_mode: bool = False, datetime_from: datetime = None, datetime_to: datetime = None):
        """
        Parameters
        ----------
        currency_pair : str
            通貨ペア("btc_jpy", etc.)
        period : str
            時間枠("1m", "5m", "15m", "30m", "1h", "4h", "8h", "12h", "1d", "1w")
        bar_count : int
            ローソク足の本数
        backtest_mode : bool, optional
            バックテストモードを実行する, by default False
        datetime_from : datetime, optional
            バックテストの開始日時, by default None
        datetime_to : datetime, optional
            バックテストの終了日時, by default None
        """

        self._currency_pair = currency_pair
        self._period = period
        self._bar_count = bar_count
        self._cache_bar_count = self._bar_count * 5
        self._backtest_mode = backtest_mode
        # バックテストモードの場合
        if self._backtest_mode:
            self._datetime_cursor = datetime_from
            self._datetime_from = datetime_from
            self._datetime_to = datetime_to
        # リアルタイムモードの場合
        else:
            self._datetime_cursor = datetime.now()
            self._datetime_from = self._datetime_cursor
            self._datetime_to = self._datetime_cursor
        self._db_context = DBContext()
        self._chart_api = ChartAPI()
        self._server_request_span = 3.0
        self._server_request_latest = None
        self._ohlcs = {}
        self._ohlc_updated_eventhandler = EventHandler(self)
        self.go_next()

    def get_ohlcs(self, extra_bar_count: int = 0) -> dict:
        """
        ローソク足を取得する

        Parameters
        ----------
        extra_bar_count : int, optional
            インディケーターが追加で必要とするローソク足の本数, by default 0

        Returns
        -------
        dict
            ローソク足
        """

        return {
            "times": self.get_times(extra_bar_count),
            "opens": self.get_prices(extra_bar_count, AppliedPrice.OPEN),
            "highs": self.get_prices(extra_bar_count, AppliedPrice.HIGH),
            "lows": self.get_prices(extra_bar_count, AppliedPrice.LOW),
            "closes": self.get_prices(extra_bar_count, AppliedPrice.CLOSE),
        }

    def get_times(self, extra_bar_count: int = 0) -> List[datetime]:
        """
        ローソク足の時刻を取得する

        Parameters
        ----------
        extra_bar_count : int
            インディケーターが追加で必要とするローソク足の本数, by default 0

        Returns
        -------
        List[datetime]
            ローソク足の時刻
        """
        bar_count = self._bar_count + extra_bar_count
        return self._ohlcs["times"][-bar_count:]

    def get_prices(self, extra_bar_count: int = 0, applied_price: AppliedPrice = AppliedPrice.CLOSE) -> numpy.ndarray:
        """
        ローソク足の価格を取得する

        Parameters
        ----------
        extra_bar_count : int, optional
            インディケーターが追加で必要とするローソク足の本数, by default 0
        applied_price : AppliedPrice, optional
            インディケーターが必要とする価格種, by default AppliedPrice.CLOSE

        Returns
        -------
        numpy.ndarray
            ローソク足の価格
        """
        bar_count = self._bar_count + extra_bar_count
        if applied_price == AppliedPrice.OPEN:
            return self._ohlcs["opens"][-bar_count:]
        elif applied_price == AppliedPrice.HIGH:
            return self._ohlcs["highs"][-bar_count:]
        elif applied_price == AppliedPrice.LOW:
            return self._ohlcs["lows"][-bar_count:]
        elif applied_price == AppliedPrice.CLOSE:
            return self._ohlcs["closes"][-bar_count:]

    def go_next(self) -> bool:
        """
        次のローソク足を取得する

        Returns
        -------
        bool
            取得に成功した場合True、失敗した場合False
        """

        # バックテストモードの場合
        if self._backtest_mode:

            if self._datetime_cursor < self._datetime_to:

                # ローソク足の取得範囲を計算する
                self._datetime_cursor += timedelta(minutes=Period.to_minutes(self._period))
                range_from = self._datetime_cursor - timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
                range_to = self._datetime_cursor

                # ローカルDBからローソク足を取得する
                ohlcs = self._get_ohlcs_from_local(range_from, range_to)

                # ローカルDBでヒットしなかった場合
                if len(ohlcs["times"]) < self._cache_bar_count:

                    # サーバーからローソク足を取得する
                    extra_range_from = range_from
                    extra_range_to = range_to + timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
                    ohlcs = self._get_ohlcs_from_server(extra_range_from, extra_range_to)

                    # キャッシュにローソク足を保存する
                    self._save_ohlcs_to_local(ohlcs)

                    # キャッシュからローソク足を取得する
                    ohlcs = self._get_ohlcs_from_local(range_from, range_to)

                # ローソク足を設定する
                self._ohlcs = ohlcs

                # ローソク足更新イベントを実行する
                self._on_ohlc_updated(EventArgs())

                return True

            else:

                return False

        # リアルタイムモードの場合
        else:

            # ローソク足の取得範囲を計算する
            self._cursor_datetime = datetime.now()
            self._to_datetime = self._cursor_datetime
            range_from = self._cursor_datetime - timedelta(minutes=Period.to_minutes(self._period) * (self._cache_bar_count - 1))
            range_to = self._cursor_datetime

            # サーバーからローソク足を取得する
            self._ohlcs = self._get_ohlcs_from_server(range_from, range_to)

            # ローソク足更新イベントを実行する
            self._on_ohlc_updated(EventArgs())

            return True

    def _get_ohlcs_from_local(self, range_from: datetime, range_to: datetime) -> dict:
        """
        ローカルDBからローソク足を取得する

        Parameters
        ----------
        range_from : datetime
            取得開始日時
        range_to : datetime
            取得終了日時

        Returns
        -------
        dict
            ローソク足
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
        ローカルDBにローソク足を保存する

        Parameters
        ----------
        ohlcs : dict
            ローソク足
        """

        # ローカルDBにローソク足を保存する
        for idx, item in enumerate(ohlcs["times"]):

            # ローカルDBにUPSERTする
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

        Parameters
        ----------
        range_from : datetime
            取得開始日時
        range_to : datetime
            取得終了日時

        Returns
        -------
        dict
            ローソク足
        """

        if self._server_request_latest:
            while self._server_request_latest + timedelta(seconds=self._server_request_span) > datetime.now():
                time.sleep(1.0)
        self._server_request_latest = datetime.now()

        response = self._chart_api.get_ohlc(self._currency_pair, Period.to_zaifapi_str(self._period), range_from, range_to)
        return {
            "times": list(map(lambda x: TimeConverter.unixtime_to_datetime(int(x["time"]/1000)), response["ohlc_data"])),
            "opens": numpy.array(list(map(lambda x: x["open"], response["ohlc_data"]))),
            "highs": numpy.array(list(map(lambda x: x["high"], response["ohlc_data"]))),
            "lows": numpy.array(list(map(lambda x: x["low"], response["ohlc_data"]))),
            "closes": numpy.array(list(map(lambda x: x["close"], response["ohlc_data"]))),
        }

    def _on_ohlc_updated(self, eargs: EventArgs):
        """
        ローソク足更新イベントを発生させます。
        """
        self._ohlc_updated_eventhandler.fire(eargs)

    @property
    def currency_pair(self) -> str:
        return self._currency_pair

    @property
    def period(self) -> str:
        return self._period

    @property
    def bar_count(self) -> str:
        return self._bar_count

    @property
    def cache_bar_count(self) -> str:
        return self._cache_bar_count

    @property
    def backtest_mode(self) -> bool:
        return self._backtest_mode

    @property
    def datetime_from(self) -> datetime:
        return self._datetime_from

    @property
    def datetime_to(self) -> datetime:
        return self._datetime_to

    @property
    def datetime_cursor(self) -> datetime:
        return self._datetime_cursor

    @property
    def ohlc_updated_eventhandler(self) -> EventHandler:
        """
        ローソク足更新イベントのハンドラ
        """
        return self._ohlc_updated_eventhandler


class Candle:
    """
    ローソク足を表します。
    """

    def __init__(self, feeder: CandleFeeder):
        self._feeder = feeder
        self._feeder.ohlc_updated_eventhandler.add(self._ohlc_updated)
        self._times = []
        self._opens = []
        self._closes = []
        self._lows = []
        self._highs = []
        self._load()

    def _load(self):
        candles = self._feeder.get_ohlcs()
        self._times = candles["times"]
        self._opens = candles["opens"].tolist()
        self._closes = candles["closes"].tolist()
        self._lows = candles["lows"].tolist()
        self._highs = candles["highs"].tolist()

    def refresh(self):
        """
        ローソク足を再読み込みします。
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
