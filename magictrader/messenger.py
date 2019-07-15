import os

import requests

from magictrader.event import TradeEventArgs
from magictrader.trade import Position, PositionRepository


class SlackMessenger:
    """
    Slackにメッセージを送信するクラス
    https://api.slack.com/methods
    """

    def __init__(self, slack_token: str, slack_channel: str, slack_username: str):

        self._slack_token = slack_token
        self._slack_channel = slack_channel
        self._slack_username = slack_username

    def send_message(self, message: str):
        """
        Slackにメッセージを送信します

        Parameters
        ----------
        message : str
            メッセージ
        """
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

    def send_position(self, position_repo: PositionRepository, position: Position, pict_path: str):

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
            position.open_comment
        )

        # 決済理由
        detail_close = "決済理由：{}"
        if position.close_time:
            detail_close = detail_close.format(
                position.close_comment
            )
        else:
            detail_close = detail_close.format(
                "-"
            )

        # 累計損益
        pl_total = int(position_repo.total_profit)
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
        self.send_file(message, pict_path)

    def position_opened(self, sender: object, eargs: TradeEventArgs):
        """
        ポジションが開かれたときに発生します。
        """
        pict_path = os.path.dirname(os.path.abspath(__file__)) + "report/chart.png"
        self.send_position(eargs.position_repo, eargs.position, pict_path)

    def position_closed(self, sender: object, eargs: TradeEventArgs):
        """
        ポジションが閉じられたときに発生します。
        """
        pict_path = os.path.dirname(os.path.abspath(__file__)) + "report/chart.png"
        self.send_position(eargs.position_repo, eargs.position, pict_path)
