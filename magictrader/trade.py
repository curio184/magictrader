import codecs
import json
from datetime import datetime, timedelta

from magictrader.utils import TimeConverter


class Position:
    """
    ポジションを表すクラス
    """

    def __init__(self):
        self._is_opened = False
        self._is_closed = False
        self._open_time = None
        self._open_action = ""
        self._open_price = None
        self._open_label = ""
        self._open_scores = {}
        self._close_time = None
        self._close_action = ""
        self._close_price = None
        self._close_label = ""
        self._close_scores = {}
        self._max_loss = 0.0
        self._max_profit = 0.0
        self._hold_period = 0

    def open(self, dt: datetime, action: str, price: float, label: str, scores: dict = None):
        self._is_opened = True
        self._open_time = dt
        self._open_action = action
        self._open_price = price
        self._open_label = label
        self._open_scores = scores

    def close(self, dt: datetime, action: str, price: float, label: str, scores: dict = None):
        self._is_closed = True
        self._close_time = dt
        self._close_action = action
        self._close_price = price
        self._close_label = label
        self._close_scores = scores

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
    def open_label(self) -> str:
        return self._open_label

    @property
    def open_scores(self) -> float:
        return self._open_scores

    @property
    def close_time(self) -> datetime:
        return self._close_time

    @property
    def close_action(self) -> str:
        return self._close_action

    @property
    def close_price(self) -> float:
        return self._close_price

    @property
    def close_label(self) -> str:
        return self._close_label

    @property
    def profit(self) -> float:
        if self._open_price and self._close_price:
            if self._open_action == "buy":
                return self._close_price - self._open_price
            else:
                return self._open_price - self._close_price
        else:
            return 0.0

    @property
    def max_loss(self) -> float:
        return self._max_loss

    @max_loss.setter
    def max_loss(self, value: float):
        self._max_loss = value

    @property
    def max_profit(self) -> float:
        return self._max_profit

    @max_profit.setter
    def max_profit(self, value: float):
        self._max_profit = value

    @property
    def hold_period(self) -> int:
        return self._hold_period

    @hold_period.setter
    def hold_period(self, value: int):
        self._hold_period = value

    def to_str(self, with_title: bool = False) -> str:

        title = ""
        if self.close_time:
            title = "MTB:PureAlpha - ポジション{}：{}".format(
                "クローズ", "買い" if self.close_action == "buy" else "売り"
            )
        else:
            title = "MTB:PureAlpha - ポジション{}：{}".format(
                "オープン", "買い" if self.open_action == "buy" else "売り"
            )

        content = "open_action:{}, open_time:{}, close_time:{}, "
        content += "open_price:{}, close_price:{}, profit:{}, "
        content += "max_profit:{}, max_loss:{}, hold_period:{}, "
        content += "open_label:{}, close_label:{}"
        content = content.format(
            self.open_action,
            TimeConverter.datetime_to_str(self.open_time) if self.open_time else "None",
            TimeConverter.datetime_to_str(self.close_time) if self.close_time else "None",
            int(self.open_price) if self.open_price else "None",
            int(self.close_price) if self.close_price else "None",
            int(self.profit) if self.profit else "None",
            self.max_profit,
            self.max_loss,
            self.hold_period,
            self.open_label if self.open_label != "" else "None",
            self.close_label if self.close_label != "" else "None"
        )

        if with_title:
            return title + "\n" + content
        else:
            return title + "\n" + content

    @staticmethod
    def to_list(positions: list) -> list:
        """
        ポジションをlistに変換する

        Parameters
        ----------
        details : list[Position]
            ポジションのリスト

        Returns
        -------
        list
            listに変換されたポジションのリスト
        """

        records = []
        for position in positions:
            records.append({
                "open_action": position.open_action,
                "open_time": "None" if not position.open_time else TimeConverter.datetime_to_str(position.open_time),
                "open_price": position.open_price,
                "open_label": position.open_label,
                "close_action": position.close_action,
                "close_time": "None" if not position.close_time else TimeConverter.datetime_to_str(position.close_time),
                "close_price": position.close_price,
                "close_label": position.close_label,
                "profit": position.profit,
                "max_profit": position.max_profit,
                "max_loss": position.max_loss,
                "hold_period": position.hold_period,
            })

        return records

    @staticmethod
    def save_as_json(positions: list, json_path: str):
        """
        ポジションをJSONに出力する

        Parameters
        ----------
        details : list[Position]
            ポジションのリスト
        json_path : str
            JSONのパス
        """

        records = Position.to_list(positions)

        with codecs.open(json_path, "w", "utf8") as f:
            json.dumps(records, f, ensure_ascii=False)
