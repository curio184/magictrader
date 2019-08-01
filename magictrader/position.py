import codecs
import json
import os
from datetime import datetime, timedelta
from typing import List

from magictrader.candle import CandleFeeder
from magictrader.const import Period
from magictrader.event import EventArgs, EventHandler


class Position:
    """
    ポジションを表します。
    """

    def __init__(self, feeder: CandleFeeder):
        """
        Parameters
        ----------
        feeder : CandleFeeder
            ローソク足のデータを提供するフィーダーです。
        """
        self._feeder = feeder
        self._is_opened = False
        self._is_closed = False
        self._is_canceled = False
        self._currency_pair = self._feeder.currency_pair
        self._open_time = None
        self._open_action = ""
        self._open_price = None
        self._open_comment = ""
        self._close_time = None
        self._close_price = None
        self._close_comment = ""
        self._order_amount = None
        self._stop_price = None
        self._limit_price = None
        self._exec_open_price = None
        self._exec_close_price = None
        self._exec_order_amount = None
        self._position_opening_eventhandler = EventHandler(self)
        self._position_closing_eventhandler = EventHandler(self)
        self._position_opened_eventhandler = EventHandler(self)
        self._position_closed_eventhandler = EventHandler(self)

    def open(self, dt: datetime, action: str, price: float, amount: float, comment: str = "",
             limit_price: float = None, stop_price: float = None):
        """
        ポジションを開きます。
        """
        self._open_time = dt
        self._open_action = action
        self._open_price = price
        self._order_amount = amount
        self._open_comment = comment
        self._limit_price = limit_price
        self._stop_price = stop_price
        opening_eargs = EventArgs(
            {"position": self, "exec_price": self._open_price, "exec_amount": self._order_amount, "cancel": False}
        )
        self._on_opening(opening_eargs)
        if opening_eargs.params["cancel"]:
            self._is_canceled = True
            return
        self._exec_open_price = opening_eargs.params["exec_price"]
        self._exec_order_amount = opening_eargs.params["exec_amount"]
        self._is_opened = True
        self._on_opened(EventArgs({"position": self}))

    def close(self, dt: datetime, price: float, comment: str = ""):
        """
        ポジションを閉じます。
        """
        self._is_closed = True
        self._close_time = dt
        self._close_price = price
        self._close_comment = comment
        closing_eargs = EventArgs(
            {"position": self, "exec_price": self._close_price}
        )
        self._on_closing(closing_eargs)
        self._exec_close_price = closing_eargs.params["exec_price"]
        self._on_closed(EventArgs({"position": self}))

    def to_dict(self) -> dict:
        """
        ポジションをdictに変換します。
        """
        data = {
            "is_opened": self._is_opened,
            "is_closed": self._is_closed,
            "is_canceled": self._is_canceled,
            "currency_pair": self._currency_pair,
            "open_time": self._open_time.strftime("%Y-%m-%d %H:%M:%S") if self._open_time else None,
            "open_action": self._open_action,
            "open_price": self._open_price,
            "open_comment": self._open_comment,
            "close_time": self._close_time.strftime("%Y-%m-%d %H:%M:%S") if self._close_time else None,
            "close_price": self._close_price,
            "close_comment": self._close_comment,
            "order_amount": self._order_amount,
            "stop_price": self._stop_price,
            "limit_price": self._limit_price,
            "exec_open_price": self._exec_open_price,
            "exec_close_price": self._exec_close_price,
            "exec_order_amount": self._exec_order_amount,
            "profit": self.profit,
        }
        return data

    def load_from_dict(self, data: dict):
        """
        dictからポジションを読み込みます。
        """
        self._is_opened = bool(data["is_opened"])
        self._is_closed = bool(data["is_closed"])
        self._is_canceled = bool(data["is_canceled"])
        self._currency_pair = str(data["currency_pair"])
        if data["open_time"] is not None:
            self._open_time = datetime.strptime(data["open_time"], "%Y-%m-%d %H:%M:%S")
        self._open_action = str(data["open_action"])
        if data["open_price"] is not None:
            self._open_price = float(data["open_price"])
        self._open_comment = str(data["open_comment"])
        if data["close_time"] is not None:
            self._close_time = datetime.strptime(data["close_time"], "%Y-%m-%d %H:%M:%S")
        if data["close_price"] is not None:
            self._close_price = float(data["close_price"])
        self._close_comment = str(data["close_comment"])
        if data["order_amount"] is not None:
            self._order_amount = float(data["order_amount"])
        if data["stop_price"] is not None:
            self._stop_price = float(data["stop_price"])
        if data["limit_price"] is not None:
            self._limit_price = float(data["limit_price"])
        if data["exec_open_price"] is not None:
            self._exec_open_price = float(data["exec_open_price"])
        if data["exec_close_price"] is not None:
            self._exec_close_price = float(data["exec_close_price"])
        if data["exec_order_amount"] is not None:
            self._exec_order_amount = float(data["exec_order_amount"])

    @property
    def is_opened(self) -> bool:
        return self._is_opened

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    @property
    def is_canceled(self) -> bool:
        return self._is_canceled

    @property
    def currency_pair(self) -> str:
        return self._currency_pair

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
            return "error"

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
    def limit_price(self) -> float:
        return self._limit_price

    @limit_price.setter
    def limit_price(self, value):
        """
        リミット価格を設定します。

        Parameters
        ----------
        value : float or None
            リミット価格を設定する場合は数値を、
            リミット価格を解除する場合はNoneを指定します。
        """
        self._limit_price = value

    @property
    def stop_price(self) -> float:
        return self._stop_price

    @stop_price.setter
    def stop_price(self, value):
        """
        ストップ価格を設定します。

        Parameters
        ----------
        value : float or None
            ストップ価格を設定する場合は数値を、
            ストップ価格を解除する場合はNoneを指定します。
        """
        self._stop_price = value

    @property
    def exec_open_price(self) -> float:
        return self._exec_open_price

    @property
    def exec_close_price(self) -> float:
        return self._exec_close_price

    @property
    def exec_order_amount(self) -> float:
        return self._exec_order_amount

    @property
    def profit(self) -> float:
        if self._is_opened and self._is_closed:
            if self._open_action == "buy":
                return self._exec_close_price - self._exec_open_price
            else:
                return self._exec_open_price - self._exec_close_price
        else:
            return 0.0

    @property
    def hold_period(self) -> int:
        """
        ポジションの保有期間を取得します。
        """
        if self._is_opened:
            hold_period = 0
            datetime_cursor = self._open_time
            datetime_to = self._close_time if self._is_closed else self._feeder.datetime_cursor
            while datetime_cursor < datetime_to:
                hold_period += 1
                datetime_cursor += timedelta(minutes=Period.to_minutes(self._feeder.period))
            return hold_period
        else:
            return 0

    def _on_opening(self, eargs: EventArgs):
        """
        ポジションオープニングイベントを発生させます。
        """
        self._position_opening_eventhandler.fire(eargs)

    def _on_closing(self, eargs: EventArgs):
        """
        ポジションクロージングイベントを発生させます。
        """
        self._position_closing_eventhandler.fire(eargs)

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
    def position_opening_eventhandler(self) -> EventHandler:
        """
        ポジションオープニングイベントのハンドラ
        """
        return self._position_opening_eventhandler

    @property
    def position_closing_eventhandler(self) -> EventHandler:
        """
        ポジションクロージングイベントのハンドラ
        """
        return self._position_closing_eventhandler

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

    def __init__(self, feeder: CandleFeeder):
        """
        Parameters
        ----------
        feeder : CandleFeeder
            ローソク足のデータを提供するフィーダーです。
        """
        self._feeder = feeder
        self._positions = []
        self._position_opening_eventhandler = EventHandler(self)
        self._position_closing_eventhandler = EventHandler(self)
        self._position_opened_eventhandler = EventHandler(self)
        self._position_closed_eventhandler = EventHandler(self)

    def create_position(self):
        position = Position(self._feeder)
        position.position_opening_eventhandler.add(self._on_position_opening)   # イベントをリレーする
        position.position_closing_eventhandler.add(self._on_position_closing)   # イベントをリレーする
        position.position_opened_eventhandler.add(self._on_position_opened)     # イベントをリレーする
        position.position_closed_eventhandler.add(self._on_position_closed)     # イベントをリレーする
        self._positions.append(position)
        return position

    def get_open_positions(self, open_action: str) -> List[Position]:
        """
        未決済建玉を取得します。
        """
        return list(filter(lambda x: x.is_opened == True
                           and x.is_closed == False
                           and x.is_canceled == False
                           and x.open_action == open_action, self._positions))

    @property
    def positions(self) -> List[Position]:
        return self._positions

    @property
    def total_profit(self) -> float:
        return sum(list(map(lambda x: x.profit, self._positions)))

    def _on_position_opening(self, sender: object, eargs: EventArgs):
        """
        ポジションオープニングイベントを発生させます。
        """
        eargs.params["position_repository"] = self
        self._position_opening_eventhandler.fire(eargs)

    def _on_position_closing(self, sender: object, eargs: EventArgs):
        """
        ポジションクロージングイベントを発生させます。
        """
        eargs.params["position_repository"] = self
        self._position_closing_eventhandler.fire(eargs)

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
    def position_opening_eventhandler(self) -> EventHandler:
        """
        ポジションオープニングイベントのハンドラ
        """
        return self._position_opening_eventhandler

    @property
    def position_closing_eventhandler(self) -> EventHandler:
        """
        ポジションクローズイベントのハンドラ
        """
        return self._position_closing_eventhandler

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

    def save_as_json(self, json_path: str):
        """
        ポジションをJSONに出力します。
        """

        records = []
        for position in self.positions:
            records.append(position.to_dict())

        with codecs.open(json_path, "w", "utf8") as f:
            json.dump(records, f, ensure_ascii=False)

    def load_from_json(self, json_path: str):
        """
        JSONからポジションを読み込みます。
        """

        if not os.path.exists(json_path):
            return

        records = None
        with codecs.open(json_path, "r", "utf8") as f:
            records = json.load(f)

        for record in records:
            position = self.create_position()
            position.load_from_dict(record)
