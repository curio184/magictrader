from datetime import datetime, timedelta
from enum import Enum


class TradeMode(Enum):

    PRACTCE = "practice"
    BACKTEST = "backtest"
    FORWARDTEST = "forwardtest"


class CurrencyPair(Enum):
    """
    通貨ペア
    """
    BTC_JPY = "btc_jpy"


class Period(Enum):
    """
    取引時間軸
    """
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    H8 = "8h"
    H12 = "12h"
    D1 = "1d"
    W1 = "1w"

    @staticmethod
    def to_minutes(period: str) -> int:

        if period == "1m":
            return 1
        elif period == "5m":
            return 5
        elif period == "15m":
            return 15
        elif period == "30m":
            return 30
        elif period == "1h":
            return 60
        elif period == "4h":
            return 240
        elif period == "8h":
            return 480
        elif period == "12h":
            return 720
        elif period == "1d":
            return 1440
        elif period == "1w":
            return 10080

    @staticmethod
    def to_zaifapi_str(period: str) -> str:

        if period == "1m":
            return "1"
        elif period == "5m":
            return "5"
        elif period == "15m":
            return "15"
        elif period == "30m":
            return "30"
        elif period == "1h":
            return "60"
        elif period == "4h":
            return "240"
        elif period == "8h":
            return "480"
        elif period == "12h":
            return "720"
        elif period == "1d":
            return "D"
        elif period == "1w":
            return "W"

    @staticmethod
    def zoom_period(period: str, zoom_level: int) -> str:

        periods = [
            {"index": 0, "name": "1m"},
            {"index": 1, "name": "5m"},
            {"index": 2, "name": "15m"},
            {"index": 3, "name": "30m"},
            {"index": 4, "name": "1h"},
            {"index": 5, "name": "4h"},
            {"index": 6, "name": "8h"},
            {"index": 7, "name": "12h"},
            {"index": 8, "name": "1d"},
            {"index": 9, "name": "1w"},
        ]

        current_period = list(filter(lambda x: x["name"] == period, periods))[0]

        zoomed_index = current_period["index"] - zoom_level

        if zoomed_index < 0:
            zoomed_index = 0
        if zoomed_index > 9:
            zoomed_index = 9

        zoomed_period = list(filter(lambda x: x["index"] == zoomed_index, periods))[0]

        return zoomed_period["name"]

    @staticmethod
    def floor_datetime(dt: datetime, period: str) -> datetime:

        if period == "1m":
            return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute)
        elif period == "5m":
            return datetime(dt.year, dt.month, dt.day, dt.hour, int(dt.minute / 5) * 5)
        elif period == "15m":
            return datetime(dt.year, dt.month, dt.day, dt.hour, int(dt.minute / 15) * 15)
        elif period == "30m":
            return datetime(dt.year, dt.month, dt.day, dt.hour, int(dt.minute / 30) * 30)
        elif period == "1h":
            return datetime(dt.year, dt.month, dt.day, dt.hour)
        elif period == "4h":
            return datetime(dt.year, dt.month, dt.day, int(dt.hour / 4) * 4)
        elif period == "8h":
            return datetime(dt.year, dt.month, dt.day, int(dt.hour / 8) * 8)
        elif period == "12h":
            return datetime(dt.year, dt.month, dt.day, int(dt.hour / 12) * 12)
        elif period == "1d":
            return datetime(dt.year, dt.month, dt.day)
        elif period == "1w":
            # 週足にも関わらず日毎に足が存在する不可解な問題があるため後回し
            return datetime(dt.year, dt.month, dt.day)

    @staticmethod
    def ceil_datetime(dt: datetime, period: str) -> datetime:

        if dt == Period.floor_datetime(dt, period):
            return dt
        else:
            return Period.floor_datetime(dt + timedelta(minutes=Period.to_minutes(period)), period)

    @staticmethod
    def get_bar_count(dt_from: datetime, dt_to: datetime, period: str) -> int:

        dt_from = Period.ceil_datetime(dt_from, period)
        dt_to = Period.floor_datetime(dt_to, period)
        minutes = ((dt_to - dt_from).days * 1440) + ((dt_to - dt_from).seconds / 60)
        bar_count = int((minutes / Period.to_minutes(period))) + 1
        return bar_count


class AppliedPrice(Enum):
    """
    テクニカルインジケーターの計算に使用する価格
    """
    OPEN = 0
    HIGH = 1
    LOW = 2
    CLOSE = 3


class ModeTRADESIGNAL(Enum):
    """
    売買シグナルの種類
    """
    BUY_OPEN = 0
    BUY_CLOSE = 1
    SELL_OPEN = 2
    SELL_CLOSE = 3


class ModeBBANDS(Enum):
    """
    ボリンジャーバンドのラインの種類
    """
    UPPER = 0
    MIDDLE = 1
    LOWER = 2


class ModeMACD(Enum):
    """
    MACDのラインの種類
    """
    FAST = 0
    SLOW = 1
    SIGNAL = 2


class ModeBAND(Enum):
    """
    BANDのラインの種類
    """
    UPPER = 0
    MIDDLE = 1
    LOWER = 2
