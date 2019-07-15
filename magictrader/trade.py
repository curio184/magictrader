from datetime import datetime
from typing import List

from magictrader.event import EventArgs, EventHandler


class Position:
    """
    ポジションを表します。
    """

    def __init__(self):
        self._is_opened = False
        self._is_closed = False
        self._open_time = None
        self._open_action = ""
        self._open_price = None
        self._open_comment = ""
        self._close_time = None
        self._close_price = None
        self._close_comment = ""
        self._order_amount = 0.0
        self._position_opened_eventhandler = EventHandler(self)
        self._position_closed_eventhandler = EventHandler(self)

    def open(self, dt: datetime, action: str, price: float, amount: float, comment: str = ""):
        """
        ポジションを開きます。
        """
        self._is_opened = True
        self._open_time = dt
        self._open_action = action
        self._open_price = price
        self._order_amount = amount
        self._open_comment = comment
        self._on_opened(EventArgs({"position": self}))

    def close(self, dt: datetime, price: float, comment: str = ""):
        """
        ポジションを閉じます。
        """
        self._is_closed = True
        self._close_time = dt
        self._close_price = price
        self._close_comment = comment
        self._on_closed(EventArgs({"position": self}))

    @property
    def is_opened(self) -> bool:
        return self._is_opened

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    @property
    def open_time(self) -> datetime:
        return self._open_time

    @property
    def open_action(self) -> str:
        return self._open_action

    @property
    def open_price(self) -> float:
        return self._open_price

    @property
    def open_comment(self) -> str:
        return self._open_comment

    @property
    def close_time(self) -> datetime:
        return self._close_time

    @property
    def close_action(self) -> str:
        if self._is_opened:
            if self._open_action == "buy":
                return "sell"
            else:
                return "buy"
        else:
            return ""

    @property
    def close_price(self) -> float:
        return self._close_price

    @property
    def close_comment(self) -> str:
        return self._close_comment

    @property
    def order_amount(self) -> float:
        return self._order_amount

    @property
    def profit(self) -> float:
        if self._is_opened and self._is_closed:
            if self._open_action == "buy":
                return self._close_price - self._open_price
            else:
                return self._open_price - self._close_price
        else:
            return 0.0

    def _on_opened(self, eargs: EventArgs):
        """
        ポジションオープンイベントを発生させます。
        """
        self._position_opened_eventhandler.fire(eargs)

    def _on_closed(self, eargs: EventArgs):
        """
        ポジションクローズイベントを発生させます。
        """
        self._position_closed_eventhandler.fire(eargs)

    @property
    def position_opened_eventhandler(self) -> EventHandler:
        """
        ポジションオープンイベントのハンドラ
        """
        return self._position_opened_eventhandler

    @property
    def position_closed_eventhandler(self) -> EventHandler:
        """
        ポジションクローズイベントのハンドラ
        """
        return self._position_closed_eventhandler


class PositionRepository:
    """
    ポジションのリポジトリを表します。
    """

    def __init__(self):
        self._positions = []
        self._position_opened_eventhandler = EventHandler(self)
        self._position_closed_eventhandler = EventHandler(self)

    def create_position(self):
        position = Position()
        position.position_opened_eventhandler.add(self._on_position_opened)   # イベントをリレーする
        position.position_closed_eventhandler.add(self._on_position_closed)   # イベントをリレーする
        self._positions.append(position)
        return position

    @property
    def positions(self) -> List[Position]:
        return self._positions

    @property
    def total_profit(self) -> float:
        return sum(list(map(lambda x: x.profit, self._positions)))

    def _on_position_opened(self, sender: object, eargs: EventArgs):
        """
        ポジションオープンイベントを発生させます。
        """
        eargs.params["position_repository"] = self
        self._position_opened_eventhandler.fire(eargs)

    def _on_position_closed(self, sender: object, eargs: EventArgs):
        """
        ポジションクローズイベントを発生させます。
        """
        eargs.params["position_repository"] = self
        self._position_closed_eventhandler.fire(eargs)

    @property
    def position_opened_eventhandler(self) -> EventHandler:
        """
        ポジションオープンイベントのハンドラ
        """
        return self._position_opened_eventhandler

    @property
    def position_closed_eventhandler(self) -> EventHandler:
        """
        ポジションクローズイベントのハンドラ
        """
        return self._position_closed_eventhandler
