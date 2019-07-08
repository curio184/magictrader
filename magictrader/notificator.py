
from typing import List

import requests

from magictrader.trade import Position


class SlackMessenger:
    """
    Slackにメッセージを送信するクラス
    https://api.slack.com/methods
    """

    def __init__(self, slack_token: str, slack_channel: str, slack_username: str, silent: bool = False):

        self._slack_token = slack_token
        self._slack_channel = slack_channel
        self._slack_username = slack_username
        self._silent = silent

    def send_message(self, message: str):
        """
        Slackにメッセージを送信します

        Parameters
        ----------
        message : str
            メッセージ
        """
        if self._silent:
            return

        try:
            param = {
                "token": self._slack_token,
                "channel": self._slack_channel,
                "username": self._slack_username,
                "text": message
            }
            requests.post(url="https://slack.com/api/chat.postMessage", params=param)
        except Exception as ex:
            print(ex)

    def send_file(self, message: str, file_path: str):
        """
        Slackに画像を送信します

        Parameters
        ----------
        message : str
            メッセージ
        file_path : str
            送信する画像のパス
        """

        if self._silent:
            return

        try:
            with open(file_path, "rb") as file_content:
                files = {"file": file_content}
                param = {
                    "token": self._slack_token,
                    "channels": self._slack_channel,
                    "username": self._slack_username,
                    "filename": file_path,
                    "initial_comment": message,
                    "title": file_path
                }
                requests.post(url="https://slack.com/api/files.upload", params=param, files=files)
        except Exception as ex:
            print(ex)

    def send_position(self, position: Position, histories: List[Position], balance_fix: float, file_path: str):

        # タイトル
        detail_title = "MTB:PureAlpha - ポジション{}：{}"
        if position.close_action == "":
            detail_title = detail_title.format(
                "オープン", "買い" if position.open_action == "buy" else "売り"
            )
        else:
            detail_title = detail_title.format(
                "クローズ", "買い" if position.close_action == "buy" else "売り"
            )

        # 期間
        detail_date = "期間　　：{} → {}"
        if position.close_time:
            if position.open_time.date == position.close_time.date:
                detail_date = detail_date.format(
                    "{0:%Y-%m-%d %H:%M:%S}".format(position.open_time),
                    "{0:%H:%M:%S}".format(position.close_time)
                )
            else:
                detail_date = detail_date.format(
                    "{0:%Y-%m-%d %H:%M:%S}".format(position.open_time),
                    "{0:%Y-%m-%d %H:%M:%S}".format(position.close_time)
                )
        else:
            detail_date = detail_date.format(
                "{0:%Y-%m-%d %H:%M:%S}".format(position.open_time),
                "未決済"
            )

        # 価格
        detail_price = "{}：{} → {}"
        if position.open_action == "buy":
            detail_price = detail_price.format(
                "ロング　",
                "{:,.0f}".format(position.open_price),
                "{:,.0f}".format(position.close_price) if position.close_price else "未決済"
            )
        else:
            detail_price = detail_price.format(
                "ショート",
                "{:,.0f}".format(position.open_price),
                "{:,.0f}".format(position.close_price) if position.close_price else "未決済"
            )

        # 損益
        detail_pl = "損益　　：{}"
        if position.close_time:
            detail_pl = detail_pl.format(
                "{:+,.0f}".format(position.profit)
            )
        else:
            detail_pl = detail_pl.format(
                "-"
            )

        # 注文理由
        detail_open = "注文理由：{}"
        detail_open = detail_open.format(
            position.open_label
        )

        # 決済理由
        detail_close = "決済理由：{}"
        if position.close_time:
            detail_close = detail_close.format(
                position.close_label
            )
        else:
            detail_close = detail_close.format(
                "-"
            )

        # 累計損益
        pl_total = int(sum(list(map(lambda x: x.profit, histories))))
        pl_total += position.profit
        pl_total += balance_fix
        detail_pl_total = "累計損益：{}"
        detail_pl_total = detail_pl_total.format(
            "{:+,.0f}".format(pl_total)
        )

        # メッセージを組み立てる
        message = ""
        message += detail_title + "\n"
        message += detail_date + "\n"
        message += detail_price + "\n"
        message += detail_pl + "\n"
        message += detail_open + "\n"
        message += detail_close + "\n"
        message += "--------------------" + "\n"
        message += detail_pl_total + "\n"

        # メッセージを送信する
        self.send_file(message, file_path)

    @property
    def silent(self) -> bool:
        return self._silent

    @silent.setter
    def silent(self, value: bool):
        self._silent = value
