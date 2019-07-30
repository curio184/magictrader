from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBAND, Period
from magictrader.indicator import ADX, ATRBAND, ENVELOPE, SMA, STDDEV
from magictrader.position import Position, PositionRepository
from magictrader.terminal import TradeTerminal


class ScoreBoard:

    def __init__(self):
        self.signal_stddev_bull = 0
        self.signal_stddev_peakout = 0
        self.signal_adx_bull = 0
        self.signal_adx_peakout = 0
        self.penalty_long_on_contrary_env = 0
        self.penalty_short_on_contrary_env = 0
        self.penalty_long_on_contrary_atrb = 0
        self.penalty_short_on_contrary_atrb = 0

    def decay(self):
        if self.signal_stddev_bull > 0:
            self.signal_stddev_bull -= 1
        if self.signal_stddev_peakout > 0:
            self.signal_stddev_peakout -= 1
        if self.signal_adx_bull > 0:
            self.signal_adx_bull -= 1
        if self.signal_adx_peakout > 0:
            self.signal_adx_peakout -= 1
        if self.penalty_long_on_contrary_env > 0:
            self.penalty_long_on_contrary_env -= 1
        if self.penalty_short_on_contrary_env > 0:
            self.penalty_short_on_contrary_env -= 1
        if self.penalty_long_on_contrary_atrb > 0:
            self.penalty_long_on_contrary_atrb -= 1
        if self.penalty_short_on_contrary_atrb > 0:
            self.penalty_short_on_contrary_atrb -= 1


class MyTradeTerminal(TradeTerminal):

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

        # テクニカルインディケーターを作成する
        sma = SMA(feeder, 13)        # SMA

        # ATRBAND
        atrb_u = ATRBAND(feeder, 13, 1.6, ModeBAND.UPPER, "atrb_u")
        atrb_l = ATRBAND(feeder, 13, 1.6, ModeBAND.LOWER, "atrb_l")

        # STDDEV
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ADX
        adx = ADX(feeder, 14, "adx")
        adx.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.indicators_left.append(sma)
        window_main.indicators_left.append(atrb_u)
        window_main.indicators_left.append(atrb_l)

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.append(stddev)
        window_sub.indicators_right.append(adx)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        # on_tickイベントに受け渡すデータを格納する
        data_bag["sma"] = sma
        data_bag["atrb_u"] = atrb_u
        data_bag["atrb_l"] = atrb_l
        data_bag["stddev"] = stddev
        data_bag["adx"] = adx

        # シグナル・ペナルティスコア
        data_bag["score_board"] = ScoreBoard()

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

        # 受け渡されたデータを引き出す
        sma = data_bag["sma"]
        atrb_u = data_bag["atrb_u"]
        atrb_l = data_bag["atrb_l"]
        stddev = data_bag["stddev"]
        adx = data_bag["adx"]

        # シグナル・ペナルティスコア
        score = data_bag["score_board"]

        # 買いストラテジーのポジション
        long_position = None
        for p in position_repository.get_open_positions("buy"):
            long_position = p
            break

        # 売りストラテジーのポジション
        short_position = None
        for p in position_repository.get_open_positions("sell"):
            short_position = p
            break

        acceleration_rate = 0.7
        risk_reward_ratio = 0.5

        # STDDEV: 上昇加速傾向
        if stddev.prices[-2] > stddev.prices[-3] \
                and stddev.prices[-1] > stddev.prices[-2] \
                and (stddev.prices[-1] - stddev.prices[-2]) > (stddev.prices[-2] - stddev.prices[-3]) * acceleration_rate:
            score.signal_stddev_bull = 3

        # STDDEV: ピークアウト
        if stddev.prices[-1] <= max(stddev.prices[-5:-1]):
            score.signal_stddev_peakout = 3

        # ADX: 上昇加速傾向
        if adx.prices[-2] > adx.prices[-3] \
                and adx.prices[-1] > adx.prices[-2] \
                and (adx.prices[-1] - adx.prices[-2]) > (adx.prices[-2] - adx.prices[-3]) * acceleration_rate:
            score.signal_adx_bull = 3

        # ADX: ピークアウト
        if adx.prices[-1] <= max(adx.prices[-5:-1]):
            score.signal_adx_peakout = 3

        # エントリー：ATR逆張り
        if not short_position:
            if score.penalty_short_on_contrary_atrb == 0 \
                    and candle.closes[-1] >= atrb_u.prices[-1] \
                    and score.signal_stddev_bull == 0 \
                    and score.signal_adx_bull == 0 \
                    and score.signal_stddev_peakout > 0 \
                    and score.signal_adx_peakout > 0:
                stop_price = candle.closes[-1] + int((candle.closes[-1] - sma.prices[-1]) * risk_reward_ratio)
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "ATR逆張り", stop_price=stop_price)

        # エントリー：ATR逆張り
        if not long_position:
            if score.penalty_long_on_contrary_atrb == 0 \
                    and candle.closes[-1] <= atrb_l.prices[-1] \
                    and score.signal_stddev_bull == 0 \
                    and score.signal_adx_bull == 0 \
                    and score.signal_stddev_peakout > 0 \
                    and score.signal_adx_peakout > 0:
                stop_price = candle.closes[-1] - int((sma.prices[-1] - candle.closes[-1]) * risk_reward_ratio)
                # ポジション
                long_position = position_repository.create_position()
                long_position.open(candle.times[-1], "buy", candle.closes[-1], 1,  "ATR逆張り", stop_price=stop_price)

        # イグジット：ATR逆張り
        if long_position \
                and long_position.open_comment == "ATR逆張り":

            # 利確：SMAタッチ
            if not long_position.is_closed:
                if candle.closes[-1] >= sma.prices[-1] and long_position.hold_period >= 0:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "SMAタッチ")

            # 損切：許容損失超過
            if not long_position.is_closed:
                if candle.closes[-1] <= long_position.stop_price and long_position.hold_period >= 0:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "許容損失超過")
                    # ペナルティスコア
                    score.penalty_long_on_contrary_atrb = 10

        # イグジット：ATR逆張り
        if short_position \
                and short_position.open_comment == "ATR逆張り":

            # 利確：SMAタッチ
            if not short_position.is_closed:
                if candle.closes[-1] <= sma.prices[-1] and short_position.hold_period >= 0:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "SMAタッチ")

            # 損切：許容損失超過
            if not short_position.is_closed:
                if candle.closes[-1] >= short_position.stop_price and short_position.hold_period >= 0:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "許容損失超過")
                    # ペナルティスコア
                    score.penalty_short_on_contrary_atrb = 10

        # シグナル・ペナルティスコアを時間経過とともに減衰させる
        if is_newbar:
            score.decay()

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
            3: ポジションを一部でも開くことに成功した場合はFalse、
               すべてキャンセルした場合はTrueを返します。
        """
        return position.open_price, position.order_amount, False

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


if __name__ == "__main__":

    # 実践モードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "1h", "practice", terminal_name="contrary_atr")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "1h", "forwardtest", terminal_name="contrary_atr")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "1h", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30), terminal_name="contrary_atr")

    mytrade.run()
