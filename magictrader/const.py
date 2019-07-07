from enum import Enum


class CurrencyPair(Enum):
    """
    通貨ペア
    """
    BTC_JPY = "btc_jpy"


class Period(Enum):
    """
    ピリオド
    """
    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    H8 = 480
    H12 = 750
    D1 = 1440
    W1 = 10080

    @staticmethod
    def to_minutes(period: str) -> int:
        if period == "5m":
            return 5

    @staticmethod
    def to_str_for_zaifapi(period: str) -> str:
        if period == "5m":
            return "5"


class APPLIED_PRICE(Enum):
    """
    テクニカルインジケーターの計算に使用する価格
    """
    OPEN = 0
    HIGH = 1
    LOW = 2
    CLOSE = 3


class MODE_BBANDS(Enum):
    UPPER = 0
    MIDDLE = 1
    LOWER = 2


class MODE_MACD(Enum):
    FAST = 0
    SLOW = 1
    SIGNAL = 2
