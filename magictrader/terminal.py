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
from magictrader.position import Position, PositionRepository
from magictrader.utils import TimeConverter


class TradeTerminal:

    def __init__(self, currency_pair: str, period: str, trade_mode: str, datetime_from: datetime = None, datetime_to: datetime = None, terminal_name: str = "mt"):
        """
        Parameters
        ----------
        currency_pair : str
            通貨ペア("btc_jpy", etc.)
        period : str
            時間枠("1m", "5m", "15m", "30m", "1h", "4h", "8h", "12h", "1d", "1w")
        trade_mode : str
            ターミナルの実行モードを指定します。
            実践モード("practice")、フォワードテスト("forwardtest")、バックテスト("backtest")のいずれかを指定します。
            バックテストを指定した場合、開始期間(datetime_from)・終了期間(datetime_to)を合わせて指定します。
        datetime_from : datetime, optional
            バックテストの開始日時, by default None
        datetime_to : datetime, optional
            バックテストの終了日時, by default None
        terminal_name : str, optional
            ターミナルの識別名, by default "mt"
        """

        # 取引の設定
        self._currency_pair = currency_pair
        self._period = period
        self._trade_mode = trade_mode
        self._datetime_from = datetime_from
        self._datetime_to = datetime_to
        self._terminal_name = terminal_name

        # INIの設定
        ini_filepath = os.path.join(os.getcwd(), "{}.ini".format(terminal_name))
        if not os.path.exists(ini_filepath):
            template_path = os.path.join(os.path.dirname(__file__), "template/mt.ini")
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
        self._position_repository = PositionRepository(self._feeder)
        if self._trade_mode == "practice":
            self._position_repository.load_from_json("{}.json".format(self._terminal_name))
            self._position_repository.position_opening_eventhandler.add(self._position_repository_position_opening)
            self._position_repository.position_closing_eventhandler.add(self._position_repository_position_closing)
        self._position_repository.position_opened_eventhandler.add(self._position_repository_position_opened)
        self._position_repository.position_closed_eventhandler.add(self._position_repository_position_closed)

    def run(self):

        data_bag = {}

        # ターミナルを初期化する
        self._on_init(self._feeder, self._chart, self._window_main, data_bag)

        # チャートを表示する
        self._chart.show()
        self._draw_position(self._position_repository)

        is_newbar = False
        evaluated_til = datetime(1900, 1, 1)

        while True:

            # タイトルを更新する
            self._window_main.title = "{} : {} - {} / total_profit : {}".format(
                self._currency_pair,
                self._candle.times[0].strftime("%Y-%m-%d %H:%M"),
                self._candle.times[-1].strftime("%Y-%m-%d %H:%M"),
                "{:+,.0f}".format(int(self._position_repository.total_profit))
            )

            # 新しい足が追加されたかどうかを評価する
            if self._candle.times[-1] > evaluated_til:
                evaluated_til = self._candle.times[-1]
                is_newbar = True

            # ティックを評価する
            self._on_tick(self._candle, data_bag, self._position_repository, is_newbar)

            is_newbar = False

            if self._trade_mode in ["practice", "forwardtest"]:
                self._chart.wait(2.0)
            self._feeder.go_next()
            self._chart.refresh()

    @abstractmethod
    def _on_init(self, feeder: CandleFeeder, chart: Chart, window_main: ChartWindow, data_bag: dict):
        """
        on_initイベントでは、
        トレードで使用するテクニカルインディケーターを作成したり、
        チャートの画面構成を定義するための初期化処理を行います。

        Parameters
        ----------
        feeder : CandleFeeder
            ローソク足のデータを提供するフィーダーです。
        chart : Chart
            チャート画面本体です。
        window_main : ChartWindow
            チャートのメイン画面です。
        data_bag : dict
            on_tickイベントに受け渡したいデータを格納します。
        """
        pass

    @abstractmethod
    def _on_tick(self, candle: Candle, data_bag: dict, position_repository: PositionRepository, is_newbar: bool):
        """
        on_tickイベントは、ローソク足のデータが更新されるたびに呼び出されます。

        Tips
        ----------
        ローソク足のデータ取得方法
        ・時刻はcandle.times[n]で取得できます。
        ・始値はcandle.opens[n]で取得できます。
        ・高値はcandle.highs[n]で取得できます。
        ・安値はcandle.lows[n]で取得できます。
        ・終値はcandle.closes[n]で取得できます。
        ※これらは時系列順のリストであり、nは0~199の数値を取ります。

        テクニカルインディケーターのデータ取得方法
        ・時刻はindicator.times[n]で取得できます。
        ・価格はindicator.prices[n]で取得できます。
        ※これらは時系列順のリストであり、nは0~199の数値を取ります。

        Parameters
        ----------
        candle : Candle
            ローソク足(OHLC)です。
        data_bag : dict
            on_initイベントから受け渡されたデータが格納されています。
            また、次のon_tickイベントに受け渡したいデータを格納します。
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ
        is_newbar : bool
            新しい足が追加された最初の呼び出し時に１度だけTrueとなります。
        """
        pass

    def _on_position_opening(self, position: Position, position_repository: PositionRepository) -> (float, float, bool):
        """
        ポジションを開くときに呼び出されます。
        ポジションをどのように開くかを実装します。

        Parameters
        ----------
        position : Position
            オープンリクエストされたポジション
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ

        Returns
        -------
        (float, float, bool)
            1: 実際の約定価格を返します。
            2: 実際の約定数量を返します。
            3: ポジションを一部でも開くことに成功した場合はTrue、
               すべてキャンセルした場合はFalseを返します。
        """
        return position.open_price, position.order_amount, True

    def _on_position_closing(self, position: Position, position_repository: PositionRepository) -> float:
        """
        ポジションを閉じるときに呼び出されます。
        ポジションをどのように閉じるかを実装します。

        Parameters
        ----------
        position : Position
            クローズリクエストされたポジション
        position_repository : PositionRepository
            ポジションを管理するためのリポジトリ

        Returns
        -------
        float
            実際の約定価格を返します。
        """
        return position.close_price

    def _position_repository_position_opening(self, sender: object, eargs: EventArgs):
        """
        リポジトリでポジションを開くときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        exec_price, exec_amount, cancel = self._on_position_opening(position, position_repository)
        eargs.params["exec_price"] = exec_price
        eargs.params["exec_amount"] = exec_amount
        eargs.params["cancel"] = cancel

    def _position_repository_position_closing(self, sender: object, eargs: EventArgs):
        """
        リポジトリでポジションを閉じるときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        exec_price = self._on_position_closing(position, position_repository)
        eargs.params["exec_price"] = exec_price

    def _position_repository_position_opened(self, sender: object, eargs: EventArgs):
        """
        リポジトリでポジションが開かれたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        position_repository.save_as_json("{}.json".format(self._terminal_name))
        self._draw_position(position_repository)
        self._send_position(position, position_repository)

    def _position_repository_position_closed(self, sender: object, eargs: EventArgs):
        """
        リポジトリでポジションが閉じられたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        position_repository.save_as_json("{}.json".format(self._terminal_name))
        self._draw_position(position_repository)
        self._send_position(position, position_repository)

    def _draw_position(self, position_repository: PositionRepository):
        """
        ポジションを描画します。
        """
        for position in position_repository.positions:
            if position.open_action == "buy":
                if position.is_opened:
                    if position.open_time in self._buy_open_signal.times:
                        idx = self._buy_open_signal.times.index(position.open_time)
                        self._buy_open_signal.prices[idx] = position.open_price
                if position.is_closed:
                    if position.close_time in self._buy_close_signal.times:
                        idx = self._buy_close_signal.times.index(position.close_time)
                        self._buy_close_signal.prices[idx] = position.close_price
            else:
                if position.is_opened:
                    if position.open_time in self._sell_open_signal.times:
                        idx = self._sell_open_signal.times.index(position.open_time)
                        self._sell_open_signal.prices[idx] = position.open_price
                if position.is_closed:
                    if position.close_time in self._sell_close_signal.times:
                        idx = self._sell_close_signal.times.index(position.close_time)
                        self._sell_close_signal.prices[idx] = position.close_price

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
        if not position.is_closed:
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
