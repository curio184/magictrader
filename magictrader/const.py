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
