import os
from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import (AppliedPrice, ModeBBANDS, ModeMACD,
                               ModeTRADESIGNAL)
from magictrader.event import EventArgs
from magictrader.indicator import (ADX, BBANDS, MACD, RSI, SMA, STDDEV,
                                   TRADESIGNAL, Indicator)
from magictrader.messenger import SlackMessenger
from magictrader.trade import Position, PositionRepository


class TradeTerminal:

    def __init__(self, currency_pair: str, period: str, trade_mode: str, datetime_from: datetime, datetime_to: datetime):

        # 取引の設定
        self._currency_pair = currency_pair
        self._period = period
        self._trade_mode = trade_mode
        self._datetime_from = datetime_from
        self._datetime_to = datetime_to

    def run(self):

        # ローソク足のフィーダーを作成する
        feeder = None
        if self._trade_mode in ["practice", "forwardtest"]:
            feeder = CandleFeeder(self._currency_pair, self._period, 200)
        elif self._trade_mode == "backtest":
            feeder = CandleFeeder(self._currency_pair, self._period, 200, True, self._datetime_from, self._datetime_to)

        # 売買シグナルインディケーターを作成する
        buy_open_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_OPEN)
        buy_close_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_CLOSE)
        sell_open_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_OPEN)
        sell_close_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_CLOSE)

        # ローソク足を作成する
        candle = Candle(feeder)

        # テクニカルインディケーターを作成する
        sma_fast = SMA(feeder, 21)
        sma_slow = SMA(feeder, 89)
        adx_fast = ADX(feeder, 13)
        adx_slow = ADX(feeder, 26)
        stddev = STDDEV(feeder, 20, 1)

        # チャート画面(メイン)を作成する
        window_main = ChartWindow()
        window_main.title = "btc_jpy"
        window_main.height_ratio = 3
        window_main.candle = candle                     # ローソク足を設定
        window_main.indicators_left.append(sma_fast)    # 短期SMAを設定
        window_main.indicators_left.append(sma_slow)    # 長期SMAを設定

        # チャート画面(サブ)を作成する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.append(adx_fast)
        window_sub.indicators_left.append(adx_slow)
        window_sub.indicators_right.append(stddev)

        # 画面を登録し、チャートを表示する
        chart = Chart()
        chart.add_window(window_main)
        chart.add_window(window_sub)
        chart.show()

        # ポジションのリポジトリを作成する
        position_repository = PositionRepository()
        position_repository.position_opened_eventhandler.add(self._position_opened)
        position_repository.position_closed_eventhandler.add(self._position_closed)

        while True:

            if sma_fast.prices[-3] < sma_slow.prices[-3]  \
                    and sma_fast.prices[-2] > sma_slow.prices[-2]:

                position = position_repository.create_position()
                position.open(candle.times[-1], "buy", candle.closes[-1], 1, "")

    def _position_opened(self, sender: object, eargs: EventArgs):
        """
        ポジションが開かれたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        self._send_position(position, position_repository)

    def _position_closed(self, sender: object, eargs: EventArgs):
        """
        ポジションが閉じられたときに発生します。
        """
        position = eargs.params["position"]
        position_repository = eargs.params["position_repository"]
        self._send_position(position, position_repository)

    def _send_position(self, position: Position, position_repository: PositionRepository):
        """
        ポジションを通知します。
        """

        # Slackの設定
        slack_token = "xoxb-393836145330-617219938608-F93SFPzgSZfD6JaxMh0MaYV8"
        slack_channel = "#general"
        slack_username = "短期売買ボット(5m)"
        slack = SlackMessenger(slack_token, slack_channel, slack_username)

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
        pict_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report")
        if not os.path.exists(pict_dir):
            os.mkdir(pict_dir)
        pict_path = os.path.join(pict_dir, "chart.png")
        self._chart.save_as_png(pict_path)

        # メッセージを送信する
        slack.send_file(message, pict_path)


if __name__ == "__main__":

    terminal = TradeTerminal("btc_jpy", "5m", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))
    terminal.run()

    # # 日時を描画
    # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
    # self._fig.autofmt_xdate()
    # # 日時を描画
    # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
    # self._fig.autofmt_xdate()
