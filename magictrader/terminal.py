import os
import shutil
from abc import ABCMeta, abstractmethod
from datetime import datetime

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeTRADESIGNAL
from magictrader.event import EventArgs
from magictrader.indicator import TRADESIGNAL
from magictrader.inifile import INIFile
from magictrader.messenger import SlackMessenger
from magictrader.trade import Position, PositionRepository


class TradeTerminal:

    def __init__(self, currency_pair: str, period: str, trade_mode: str, datetime_from: datetime, datetime_to: datetime, ini_filename: str = "mt.ini"):

        # 取引の設定
        self._currency_pair = currency_pair
        self._period = period
        self._trade_mode = trade_mode
        self._datetime_from = datetime_from
        self._datetime_to = datetime_to

        # INIの設定
        ini_filepath = os.path.join(os.getcwd(), ini_filename)
        if not os.path.exists(ini_filename):
            template_path = os.path.join(os.path.dirname(__file__), "config/mt.ini")
            shutil.copy(template_path, ini_filepath)
        self._inifile = INIFile(ini_filepath)

        # ローソク足のフィーダーを作成する
        if self._trade_mode in ["practice", "forwardtest"]:
            self._feeder = CandleFeeder(self._currency_pair, self._period, 200)
        elif self._trade_mode == "backtest":
            self._feeder = CandleFeeder(self._currency_pair, self._period, 200, True, self._datetime_from, self._datetime_to)

        # 売買シグナルインディケーターを作成する
        self._buy_open_signal = TRADESIGNAL(self._feeder, ModeTRADESIGNAL.BUY_OPEN)
        self._buy_close_signal = TRADESIGNAL(self._feeder, ModeTRADESIGNAL.BUY_CLOSE)
        self._sell_open_signal = TRADESIGNAL(self._feeder, ModeTRADESIGNAL.SELL_OPEN)
        self._sell_close_signal = TRADESIGNAL(self._feeder, ModeTRADESIGNAL.SELL_CLOSE)

        # ローソク足を作成する
        self._candle = Candle(self._feeder)

        # チャートを作成する
        self._chart = Chart()

        # チャート(メイン画面)を作成する
        self._window_main = ChartWindow()
        self._window_main.title = self._currency_pair
        self._window_main.height_ratio = 3
        self._window_main.candle = self._candle     # ローソク足を設定
        self._window_main.indicators_left.append(self._buy_open_signal)
        self._window_main.indicators_left.append(self._buy_close_signal)
        self._window_main.indicators_left.append(self._sell_open_signal)
        self._window_main.indicators_left.append(self._sell_close_signal)

        # チャートにメイン画面を登録する
        self._chart.add_window(self._window_main)

        # ポジションのリポジトリを作成する
        self._position_repository = PositionRepository()
        self._position_repository.position_opened_eventhandler.add(self._position_opened)
        self._position_repository.position_closed_eventhandler.add(self._position_closed)

    def run(self):

        data_bag = {}

        # ターミナルを初期化する
        self._on_init(self._feeder, self._chart, self._window_main, data_bag)

        # チャートを表示する
        self._chart.show()

        while True:
            self._on_tick(self._candle, data_bag, self._position_repository)
            self._feeder.go_next()
            self._chart.refresh()

    @abstractmethod
    def _on_init(self, feeder: CandleFeeder, chart: Chart, window_main: ChartWindow, data_bag: dict):
        pass

    @abstractmethod
    def _on_tick(self, candle: Candle, data_bag: dict, position_repository: PositionRepository):
        pass

    def _position_opened(self, sender: object, eargs: EventArgs):
        """
        ポジションが開かれたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        self._draw_position(position)
        self._send_position(position, position_repository)

    def _position_closed(self, sender: object, eargs: EventArgs):
        """
        ポジションが閉じられたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        self._draw_position(position)
        self._send_position(position, position_repository)

    def _draw_position(self, position: Position):
        """
        ポジションを描画する
        """
        if position.open_action == "buy":
            if position.is_closed:
                self._buy_close_signal.prices[-1] = position.close_price
            else:
                self._buy_open_signal.prices[-1] = position.open_price
        else:
            if position.is_closed:
                self._sell_close_signal.prices[-1] = position.close_price
            else:
                self._sell_open_signal.prices[-1] = position.open_price

        self._chart.refresh()

    def _send_position(self, position: Position, position_repository: PositionRepository):
        """
        ポジションを通知します。
        """

        # Slackの設定
        if not self._inifile.get_bool("slack", "enabled", False):
            return
        slack_token = self._inifile.get_str("slack", "token", "")
        slack_channel = self._inifile.get_str("slack", "channel", "")
        slack_username = self._inifile.get_str("slack", "username", "")
        slack = SlackMessenger(slack_token, slack_channel, slack_username)

        # タイトル
        detail_title = slack_username + " - ポジション{}：{}"
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
        pl_total = int(position_repository.total_profit)
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

        # チャートを画像として保存する
        pict_dir = os.path.join(os.getcwd(), "report")
        if not os.path.exists(pict_dir):
            os.mkdir(pict_dir)
        pict_path = os.path.join(pict_dir, "chart.png")
        self._chart.save_as_png(pict_path)

        # メッセージを送信する
        slack.send_file(message, pict_path)
