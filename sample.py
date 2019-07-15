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

    def start(self):

        # ローソク足のフィーダーを作成する
        feeder = None
        if self._trade_mode in ["practice", "forwardtest"]:
            feeder = CandleFeeder(self._currency_pair, self._period, 200)
        elif self._trade_mode == "backtest":
            feeder = CandleFeeder(self._currency_pair, self._period, 200, True, self._datetime_from, self._datetime_to)

        # ローソク足を作成する
        candle = Candle(feeder)

        # 売買シグナルインディケーターを作成する
        buy_open_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_OPEN)
        buy_close_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_CLOSE)
        sell_open_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_OPEN)
        sell_close_signal = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_CLOSE)

        # テクニカルインディケーターを作成する
        sma_fast = SMA(feeder, 21)
        sma_slow = SMA(feeder, 89)
        adx_fast = ADX(feeder, 13)
        adx_slow = ADX(feeder, 26)
        stddev = STDDEV(feeder, 20, 1, AppliedPrice.CLOSE)

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

        # Slack
        slack_token = "xoxb-393836145330-617219938608-F93SFPzgSZfD6JaxMh0MaYV8"
        slack_channel = "#general"
        slack_username = "短期売買ボット(5m)"
        slack = SlackMessenger(slack_token, slack_channel, slack_username)

        # ポジションのリポジトリを作成する
        position_repo = PositionRepository()
        position_repo.position_opened_eventhandler.add(buy_open_signal.position_opened)
        position_repo.position_opened_eventhandler.add(sell_open_signal.position_opened)
        position_repo.position_opened_eventhandler.add(chart.position_opened)
        position_repo.position_opened_eventhandler.add(slack.position_opened)
        position_repo.position_opened_eventhandler.add(buy_close_signal.position_closed)
        position_repo.position_opened_eventhandler.add(sell_close_signal.position_closed)
        position_repo.position_closed_eventhandler.add(chart.position_closed)
        position_repo.position_closed_eventhandler.add(slack.position_closed)

        while True:

            if sma_slow.prices[-3] < sma_fast.prices[-3]  \
                    and sma_slow.prices[-2] > sma_fast.prices[-2]:

                position = position_repo.create_position()
                position.open(candle.times[-1], "buy", candle.closes[-1], 1, "")

            feeder.go_next()
            chart.refresh()

        pict_path = ""
        chart.save_as_png(pict_path)


if __name__ == "__main__":

    terminal = TradeTerminal("btc_jpy", "5m", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))
    terminal.start()

    # # 日時を描画
    # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
    # self._fig.autofmt_xdate()
    # # 日時を描画
    # self._ax[0].set_xticklabels(list(map(lambda x: "{0:%H:%M}".format(x), candle.times)), rotation=0)
    # self._fig.autofmt_xdate()
