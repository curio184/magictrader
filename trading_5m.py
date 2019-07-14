import time
from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import (AppliedPrice, ModeBBANDS, ModeMACD,
                               ModeTRADESIGNAL)
from magictrader.indicator import (ADX, BBANDS, ENVELOPE, MACD, RSI, SMA,
                                   STDDEV, TRADESIGNAL)
from magictrader.notificator import SlackMessenger
from magictrader.trade import Position


class TradeTerminal:

    def __init__(self, currency_pair: str, period: str, trade_mode: str, datetime_from: datetime, datetime_to: datetime, slack: SlackMessenger, balance_fix: float):

        self._currency_pair = currency_pair
        self._period = period
        self._trade_mode = trade_mode
        self._datetime_from = datetime_from
        self._datetime_to = datetime_to

        self._slack = slack
        self._balance_fix = 0

    def start(self):

        # 買いストラテジーのポジション
        buy_positions = []
        buy_current_position = None

        # 売りストラテジーのポジション
        sell_positions = []
        sell_current_position = None

        # 買いストラテジーのシグナルスコア
        buy_open_score_bull_trend = 0
        buy_open_score_bb_p1 = 0
        buy_open_score_bb_m1 = 0
        buy_open_score_stddev_bull = 0
        buy_open_score_stddev_bear = 0
        buy_open_score_adx_bull = 0
        buy_open_score_adx_bear = 0
        buy_open_score_sma_gc_fast_middle = 0
        buy_open_score_sma_gc_fast_slow = 0
        buy_open_score_env_touch = 0
        buy_open_score_bb_penalty = 0
        buy_open_score_env_penalty = 0

        # 売りストラテジーのシグナルスコア
        sell_is_ready = False
        sell_open_score_bear_trend = 0
        sell_open_score_bb_p1 = 0
        sell_open_score_bb_m1 = 0
        sell_open_score_stddev_bull = 0
        sell_open_score_stddev_bear = 0
        sell_open_score_adx_bull = 0
        sell_open_score_adx_bear = 0
        sell_open_score_sma_dc_fast_middle = 0
        sell_open_score_sma_dc_fast_slow = 0
        sell_open_score_env_touch = 0
        sell_open_score_bb_penalty = 0
        sell_open_score_env_penalty = 0

        # ローソク足のフィーダー
        feeder = CandleFeeder(self._currency_pair, self._period, 200, True, datetime(2019, 3, 1), datetime(2019, 6, 30))
        # feeder = CandleFeeder(self._currency_pair, self._period, 200)

        # 売買シグナルインディケーター
        buy_signal_open = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_OPEN)
        buy_signal_close = TRADESIGNAL(feeder, ModeTRADESIGNAL.BUY_CLOSE)
        sell_signal_open = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_OPEN)
        sell_signal_close = TRADESIGNAL(feeder, ModeTRADESIGNAL.SELL_CLOSE)

        # ローソク足を取得する
        candle = Candle(feeder)

        # SMAを取得する
        sma_fast = SMA(feeder, 5, "sma_fast")
        sma_middle = SMA(feeder, 21, "sma_middle")
        sma_slow = SMA(feeder, 89, "sma_slow")

        # BBを取得する
        bb_p3 = BBANDS(feeder, 21, 3, ModeBBANDS.UPPER, "bb_p3")
        bb_p2 = BBANDS(feeder, 21, 2, ModeBBANDS.UPPER, "bb_p2")
        bb_p1 = BBANDS(feeder, 21, 1, ModeBBANDS.UPPER, "bb_p1")
        bb_md = BBANDS(feeder, 21, 1, ModeBBANDS.MIDDLE, "bb_midle")
        bb_m1 = BBANDS(feeder, 21, 1, ModeBBANDS.LOWER, "bb_m1")
        bb_m2 = BBANDS(feeder, 21, 2, ModeBBANDS.LOWER, "bb_m2")
        bb_m3 = BBANDS(feeder, 21, 3, ModeBBANDS.LOWER, "bb_m3")

        # ADXを取得する
        adx_fast = ADX(feeder, 13)
        adx_fast.label = "adx_fast"
        adx_fast.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        adx_slow = ADX(feeder, 26)
        adx_slow.label = "adx_slow"
        adx_slow.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}

        # STDDEVを取得する
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ENVELOPEを取得する
        dev_rate1 = 0.011
        dev_rate2 = 0.015
        env_u2 = ENVELOPE(feeder, 26, dev_rate2, "env_u2")
        env_u2.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}
        env_u1 = ENVELOPE(feeder, 26, dev_rate1, "env_u1")
        env_u1.style = {"linestyle": "dashdot", "color": "grey", "linewidth": 0.5, "alpha": 1}
        env_md = ENVELOPE(feeder, 26, 0, "env_md")
        env_md.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}
        env_l1 = ENVELOPE(feeder, 26, -dev_rate1, "env_l1")
        env_l1.style = {"linestyle": "dashdot", "color": "grey", "linewidth": 0.5, "alpha": 1}
        env_l2 = ENVELOPE(feeder, 26, -dev_rate2, "env_l2")
        env_l2.style = {"linestyle": "dashdot", "color": "red", "linewidth": 0.5, "alpha": 1}

        # チャート
        chart = Chart()

        # チャート(メインウィンドウ)
        window_main = ChartWindow()
        window_main.title = "btc_jpy"
        window_main.height_ratio = 3
        window_main.candle = candle
        window_main.indicators_left.extend(
            [buy_signal_open, buy_signal_close, sell_signal_open, sell_signal_close,
             sma_fast, sma_middle, sma_slow,
             bb_p3, bb_p2, bb_p1, bb_md, bb_m1, bb_m2, bb_m3,
             env_u2, env_u1, env_md, env_l1, env_l2]
        )
        chart.add_window(window_main)

        # チャート(サブウインドウ)
        window_sub = ChartWindow()
        window_sub.indicators_left.extend([adx_fast, adx_slow])
        window_sub.indicators_right.append(stddev)
        chart.add_window(window_sub)

        chart.show()

        evaluated_til = datetime(1900, 1, 1)

        shouldstop = False
        while not shouldstop:

            ##################################################
            # 買いストラテジー
            ##################################################

            up_ratio = 0.7

            # トリガー(BB: +1σ上抜け) ⇒ 足の確定を待たない
            if candle.closes[-2] < bb_p1.prices[-2] \
                    and candle.closes[-1] > bb_p1.prices[-1]:
                buy_open_score_bb_p1 = 5

            # トリガー(BB: -1σ下抜け) ⇒ 足の確定を待たない
            if candle.closes[-2] > bb_m1.prices[-2] \
                    and candle.closes[-1] < bb_m1.prices[-1]:
                buy_open_score_bb_m1 = 5

            # トリガー(SMA: ゴールデンクロス fast/middle) ⇒ 足の確定を待つ
            if sma_fast.prices[-3] < sma_middle.prices[-3] \
                    and sma_fast.prices[-2] > sma_middle.prices[-2]:
                buy_open_score_sma_gc_fast_middle = 5

            # トリガー(SMA: ゴールデンクロス fast/slow) ⇒ 足の確定を待つ
            if sma_fast.prices[-3] < sma_slow.prices[-3] \
                    and sma_fast.prices[-2] > sma_slow.prices[-2]:
                buy_open_score_sma_gc_fast_slow = 5

            # トリガー(STDDEV: 上昇加速傾向) ⇒ 足の確定を待たない
            if stddev.prices[-2] > stddev.prices[-3] \
                    and stddev.prices[-1] > stddev.prices[-2] \
                    and (stddev.prices[-1] - stddev.prices[-2]) > (stddev.prices[-2] - stddev.prices[-3]) * up_ratio:
                buy_open_score_stddev_bull = 3

            # トリガー(STDDEV: 下降加速傾向) ⇒ 足の確定を待たない
            if stddev.prices[-2] < stddev.prices[-3] \
                    and stddev.prices[-1] < stddev.prices[-2] \
                    and (stddev.prices[-2] - stddev.prices[-1]) > (stddev.prices[-3] - stddev.prices[-2]) * up_ratio:
                buy_open_score_stddev_bear = 3

            # トリガー(ADX: 上昇加速傾向) ⇒ 足の確定を待たない
            if adx_slow.prices[-2] > adx_slow.prices[-3] \
                    and adx_slow.prices[-1] > adx_slow.prices[-2] \
                    and (adx_slow.prices[-1] - adx_slow.prices[-2]) > (adx_slow.prices[-2] - adx_slow.prices[-3]) * up_ratio:
                buy_open_score_adx_bull = 3

            # トリガー(ADX: 下降加速傾向) ⇒ 足の確定を待たない
            if adx_slow.prices[-2] < adx_slow.prices[-3] \
                    and adx_slow.prices[-1] < adx_slow.prices[-2] \
                    and (adx_slow.prices[-2] - adx_slow.prices[-1]) > (adx_slow.prices[-3] - adx_slow.prices[-2]) * up_ratio:
                buy_open_score_adx_bear = 3

            # トリガー(ENV: マイナス乖離1タッチ) ⇒ 足の確定を持たない
            if candle.lows[-1] < env_l1.prices[-1] \
                    and candle.lows[-1] > env_l2.prices[-1]:
                buy_open_score_env_touch = 1

            # 標準偏差順張りに反応するためのフィルタ
            # フィルタ(BB: +1σ上が継続中)
            # フィルタ(ADX: 上昇加速傾向)
            if not buy_current_position:
                if candle.closes[-1] > bb_p1.prices[-1] \
                        and buy_open_score_bb_p1 > 0 \
                        and buy_open_score_adx_bull > 0 \
                        and buy_open_score_stddev_bull > 0 \
                        and buy_open_score_bb_penalty == 0:
                    # チャートの更新
                    buy_signal_open.prices[-1] = candle.closes[-1]
                    # ポジションの更新
                    buy_current_position = Position()
                    buy_current_position.open(candle.times[-1], "buy", candle.closes[-1], "標準偏差順張り")
                    # Slackの更新
                    if self._trade_mode == "practice":
                        chart.save_as_png("report/chart.png")
                        self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                    # スコアの更新
                    buy_open_score_bull_trend = 20
                    buy_open_score_bb_p1 = 0
                    buy_open_score_bb_m1 = 0
                    buy_open_score_stddev_bull = 0
                    buy_open_score_stddev_bear = 0
                    buy_open_score_adx_bull = 0
                    buy_open_score_adx_bear = 0
                    buy_open_score_sma_gc_fast_middle = 0
                    buy_open_score_sma_gc_fast_slow = 0
                    buy_open_score_env_touch = 0

            # エンベロープ逆張りに反応するためのフィルタ
            # フィルタ(ENV: マイナス乖離1にタッチ)
            # フィルタ(BB/ADX/STD: 売りトレンドが発生していない)
            if not buy_current_position:
                if buy_open_score_env_touch > 0 \
                        and buy_open_score_env_penalty == 0 \
                        and not (buy_open_score_bb_m1 > 0
                                 and buy_open_score_adx_bull > 0
                                 and buy_open_score_stddev_bull > 0):
                    # チャートの更新
                    buy_signal_open.prices[-1] = candle.closes[-1]
                    # ポジションの更新
                    buy_current_position = Position()
                    buy_current_position.open(candle.times[-1], "buy", candle.closes[-1], "エンベロープ逆張り")
                    # Slackの更新
                    if self._trade_mode == "practice":
                        chart.save_as_png("report/chart.png")
                        self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                    # スコアの更新
                    buy_open_score_bb_p1 = 0
                    buy_open_score_bb_m1 = 0
                    buy_open_score_stddev_bull = 0
                    buy_open_score_stddev_bear = 0
                    buy_open_score_adx_bull = 0
                    buy_open_score_adx_bear = 0
                    buy_open_score_sma_gc_fast_middle = 0
                    buy_open_score_sma_gc_fast_slow = 0
                    buy_open_score_env_touch = 0

            # １時間足につき、１度だけ実行する
            if candle.times[-1] > evaluated_til:

                # スコアの減衰
                if buy_open_score_bull_trend > 0:
                    buy_open_score_bull_trend -= 1
                if buy_open_score_bb_p1 > 0:
                    buy_open_score_bb_p1 -= 1
                if buy_open_score_bb_m1 > 0:
                    buy_open_score_bb_m1 -= 1
                if buy_open_score_bb_penalty > 0:
                    buy_open_score_bb_penalty -= 1
                if buy_open_score_stddev_bull > 0:
                    buy_open_score_stddev_bull -= 1
                if buy_open_score_stddev_bear > 0:
                    buy_open_score_stddev_bear -= 1
                if buy_open_score_adx_bull > 0:
                    buy_open_score_adx_bull -= 1
                if buy_open_score_adx_bear > 0:
                    buy_open_score_adx_bear -= 1
                if buy_open_score_sma_gc_fast_middle > 0:
                    buy_open_score_sma_gc_fast_middle -= 1
                if buy_open_score_sma_gc_fast_slow > 0:
                    buy_open_score_sma_gc_fast_slow -= 1
                if buy_open_score_env_touch > 0:
                    buy_open_score_env_touch -= 1
                if buy_open_score_env_penalty > 0:
                    buy_open_score_env_penalty -= 1

            # ポジション統計の取得
            if buy_current_position:

                # 最大含み益
                if candle.highs[-1] > buy_current_position.open_price:
                    if candle.highs[-1] - buy_current_position.open_price > buy_current_position.max_profit:
                        buy_current_position.max_profit = \
                            candle.highs[-1] - buy_current_position.open_price

                # 最大含み損
                if candle.lows[-1] < buy_current_position.open_price:
                    if candle.lows[-1] - buy_current_position.open_price < buy_current_position.max_loss:
                        buy_current_position.max_loss = \
                            candle.lows[-1] - buy_current_position.open_price

                # ホールド期間
                if candle.times[-1] != buy_current_position.open_time \
                        and candle.times[-1] > evaluated_til:
                    buy_current_position.hold_period += 1

            # クローズ(label="標準偏差順張り")
            if buy_current_position \
                    and buy_current_position.open_label == "標準偏差順張り":

                # 利確トリガー(BB: +1σ下抜け) ⇒ 足の確定を待つ
                if buy_current_position and buy_current_position.hold_period >= 4:
                    if candle.closes[-2] < bb_p1.prices[-2]:
                        # チャートの更新
                        buy_signal_close.prices[-1] = candle.opens[-1]
                        # ポジションの更新
                        buy_current_position.close(candle.times[-1], "sell", candle.opens[-1], "+1σ下抜け")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # スコアの更新
                        if buy_current_position.hold_period <= 10:
                            buy_open_score_bb_penalty = 10 - buy_current_position.hold_period
                        # ポジション履歴の更新
                        buy_positions.append(buy_current_position)
                        buy_current_position = None

                # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
                if buy_current_position and buy_current_position.hold_period >= 1:
                    if candle.closes[-1] < sma_middle.prices[-1]:
                        # チャートの更新
                        buy_signal_close.prices[-1] = sma_middle.prices[-1]
                        # ポジションの更新
                        buy_current_position.close(candle.times[-1], "sell", sma_middle.prices[-1], "sma_middleタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        buy_positions.append(buy_current_position)
                        buy_current_position = None

            # クローズ(label="エンベロープ逆張り")
            if buy_current_position \
                    and buy_current_position.open_label == "エンベロープ逆張り":

                # 利確トリガー(ENV: env_mdタッチ) ⇒ 足の確定を待たない
                if buy_current_position and buy_current_position.hold_period >= 1:
                    if candle.highs[-1] > env_md.prices[-1]:
                        # チャートの更新
                        buy_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        buy_current_position.close(candle.times[-1], "sell", candle.closes[-1], "env_mdタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        buy_positions.append(buy_current_position)
                        buy_current_position = None

                # 損切りトリガー(ENV: 建値割込み) ⇒ 足の確定を待たない
                if buy_current_position and buy_current_position.hold_period >= 4:
                    if candle.lows[-1] < buy_current_position.open_price:
                        # チャートの更新
                        buy_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        buy_current_position.close(candle.times[-1], "sell", candle.closes[-1], "同値撤退")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # スコアの更新
                        buy_open_score_env_penalty = 30
                        # ポジション履歴の更新
                        buy_positions.append(buy_current_position)
                        buy_current_position = None

                # 損切りトリガー(ENV: マイナス乖離2タッチ) ⇒ 足の確定を待たない
                if buy_current_position and buy_current_position.hold_period >= 0:
                    if candle.lows[-1] < env_l2.prices[-1]:
                        # チャートの更新
                        buy_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        buy_current_position.close(candle.times[-1], "sell", candle.closes[-1], "マイナス乖離2タッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(buy_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # スコアの更新
                        buy_open_score_env_penalty = 30
                        # ポジション履歴の更新
                        buy_positions.append(buy_current_position)
                        buy_current_position = None

            ##################################################
            # 売りストラテジー
            ##################################################

            up_ratio = 0.7

            # フィルタ(戻り高値を達成)
            if candle.highs[-2] >= sma_middle.prices[-2] \
                    or candle.highs[-2] >= sma_slow.prices[-2]:
                sell_is_ready = True

            # トリガー(BB: +1σ上抜け) ⇒ 足の確定を待たない
            if candle.closes[-2] < bb_p1.prices[-2] \
                    and candle.closes[-1] > bb_p1.prices[-1]:
                sell_open_score_bb_p1 = 5

            # トリガー(BB: -1σ下抜け) ⇒ 足の確定を待たない
            if candle.closes[-2] > bb_m1.prices[-2] \
                    and candle.closes[-1] < bb_m1.prices[-1]:
                sell_open_score_bb_m1 = 5

            # トリガー(SMA: デッドクロス fast/middle) ⇒ 足の確定を待つ
            if sma_fast.prices[-3] > sma_middle.prices[-3] \
                    and sma_fast.prices[-2] < sma_middle.prices[-2]:
                sell_open_score_sma_dc_fast_middle = 5

            # トリガー(SMA: デッドクロス fast/slow) ⇒ 足の確定を待つ
            if sma_fast.prices[-3] > sma_slow.prices[-3] \
                    and sma_fast.prices[-2] < sma_slow.prices[-2]:
                sell_open_score_sma_dc_fast_slow = 5

            # トリガー(STDDEV: 上昇加速傾向) ⇒ 足の確定を待たない
            if stddev.prices[-2] > stddev.prices[-3] \
                    and stddev.prices[-1] > stddev.prices[-2] \
                    and (stddev.prices[-1] - stddev.prices[-2]) > (stddev.prices[-2] - stddev.prices[-3]) * up_ratio:
                sell_open_score_stddev_bull = 3

            # トリガー(STDDEV: 下降加速傾向) ⇒ 足の確定を待たない
            if stddev.prices[-2] < stddev.prices[-3] \
                    and stddev.prices[-1] < stddev.prices[-2] \
                    and (stddev.prices[-2] - stddev.prices[-1]) > (stddev.prices[-3] - stddev.prices[-2]) * up_ratio:
                sell_open_score_stddev_bear = 3

            # トリガー(ADX: 上昇加速傾向) ⇒ 足の確定を待たない
            if adx_slow.prices[-2] > adx_slow.prices[-3] \
                    and adx_slow.prices[-1] > adx_slow.prices[-2] \
                    and (adx_slow.prices[-1] - adx_slow.prices[-2]) > (adx_slow.prices[-2] - adx_slow.prices[-3]) * up_ratio:
                sell_open_score_adx_bull = 3

            # トリガー(ADX: 下降加速傾向) ⇒ 足の確定を待たない
            if adx_slow.prices[-2] < adx_slow.prices[-3] \
                    and adx_slow.prices[-1] < adx_slow.prices[-2] \
                    and (adx_slow.prices[-2] - adx_slow.prices[-1]) > (adx_slow.prices[-3] - adx_slow.prices[-2]) * up_ratio:
                sell_open_score_adx_bear = 3

            # トリガー(ENV: プラス乖離1タッチ) ⇒ 足の確定を持たない
            if candle.highs[-1] > env_u1.prices[-1] \
                    and candle.highs[-1] < env_u2.prices[-1]:
                sell_open_score_env_touch = 1

            # 調整下げに反応するためのフィルタ
            # フィルタ(BB: -1σ下が継続中)
            # フィルタ(すべてのトリガーが発動中)
            if not sell_current_position:
                if sell_is_ready \
                        and candle.closes[-1] < bb_m1.prices[-1] \
                        and sell_open_score_bb_m1 > 0 \
                        and sell_open_score_adx_bear > 0 \
                        and sell_open_score_stddev_bear > 0 \
                        and sell_open_score_sma_dc_fast_middle > 0 \
                        and sell_open_score_sma_dc_fast_slow > 0:
                        # チャートの更新
                    sell_signal_open.prices[-1] = candle.closes[-1]
                    # ポジションの更新
                    sell_current_position = Position()
                    sell_current_position.open(candle.times[-1], "sell", candle.closes[-1], "調整局面のデッドクロス")
                    # Slackの更新
                    if self._trade_mode == "practice":
                        chart.save_as_png("report/chart.png")
                        self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                    # スコアの更新
                    sell_is_ready = False
                    sell_open_score_bb_p1 = 0
                    sell_open_score_bb_m1 = 0
                    sell_open_score_stddev_bull = 0
                    sell_open_score_stddev_bear = 0
                    sell_open_score_adx_bull = 0
                    sell_open_score_adx_bear = 0
                    sell_open_score_sma_dc_fast_middle = 0
                    sell_open_score_sma_dc_fast_slow = 0
                    sell_open_score_env_touch = 0

            # 標準偏差順張りに反応するためのフィルタ
            # フィルタ(BB: -1σ下が継続中)
            # フィルタ(ADX: 上昇加速傾向)
            if not sell_current_position:
                if sell_is_ready \
                        and candle.closes[-1] < bb_m1.prices[-1] \
                        and sell_open_score_bb_m1 > 0 \
                        and sell_open_score_adx_bull > 0 \
                        and sell_open_score_stddev_bull > 0 \
                        and sell_open_score_bb_penalty == 0:
                    # チャートの更新
                    sell_signal_open.prices[-1] = candle.closes[-1]
                    # ポジションの更新
                    sell_current_position = Position()
                    sell_current_position.open(candle.times[-1], "sell", candle.closes[-1], "標準偏差順張り")
                    # Slackの更新
                    if self._trade_mode == "practice":
                        chart.save_as_png("report/chart.png")
                        self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                    # スコアの更新
                    sell_is_ready = False
                    sell_open_score_bear_trend = 20
                    sell_open_score_bb_p1 = 0
                    sell_open_score_bb_m1 = 0
                    sell_open_score_stddev_bull = 0
                    sell_open_score_stddev_bear = 0
                    sell_open_score_adx_bull = 0
                    sell_open_score_adx_bear = 0
                    sell_open_score_sma_dc_fast_middle = 0
                    sell_open_score_sma_dc_fast_slow = 0
                    sell_open_score_env_touch = 0

            # エンベロープ逆張りに反応するためのフィルタ
            # フィルタ(ENV: マイナス乖離1にタッチ)
            # フィルタ(BB/ADX/STD: 買いトレンドが発生していない)
            if not sell_current_position:
                if sell_open_score_env_touch > 0 \
                    and sell_open_score_env_penalty == 0 \
                    and not (sell_open_score_bb_p1 > 0
                             and sell_open_score_adx_bull > 0
                             and sell_open_score_stddev_bull > 0):
                    # チャートの更新
                    sell_signal_open.prices[-1] = candle.closes[-1]
                    # ポジションの更新
                    sell_current_position = Position()
                    sell_current_position.open(candle.times[-1], "sell", candle.closes[-1], "エンベロープ逆張り")
                    # Slackの更新
                    if self._trade_mode == "practice":
                        chart.save_as_png("report/chart.png")
                        self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                    # スコアの更新
                    sell_is_ready = False
                    sell_open_score_bb_p1 = 0
                    sell_open_score_bb_m1 = 0
                    sell_open_score_stddev_bull = 0
                    sell_open_score_stddev_bear = 0
                    sell_open_score_adx_bull = 0
                    sell_open_score_adx_bear = 0
                    sell_open_score_sma_dc_fast_middle = 0
                    sell_open_score_sma_dc_fast_slow = 0
                    sell_open_score_env_touch = 0

            # １時間足につき、１度だけ実行する
            if candle.times[-1] > evaluated_til:

                # スコアの減衰
                if sell_open_score_bear_trend > 0:
                    sell_open_score_bear_trend -= 1
                if sell_open_score_bb_p1 > 0:
                    sell_open_score_bb_p1 -= 1
                if sell_open_score_bb_m1 > 0:
                    sell_open_score_bb_m1 -= 1
                if sell_open_score_bb_penalty > 0:
                    sell_open_score_bb_penalty -= 1
                if sell_open_score_stddev_bull > 0:
                    sell_open_score_stddev_bull -= 1
                if sell_open_score_stddev_bear > 0:
                    sell_open_score_stddev_bear -= 1
                if sell_open_score_adx_bull > 0:
                    sell_open_score_adx_bull -= 1
                if sell_open_score_adx_bear > 0:
                    sell_open_score_adx_bear -= 1
                if sell_open_score_sma_dc_fast_middle > 0:
                    sell_open_score_sma_dc_fast_middle -= 1
                if sell_open_score_sma_dc_fast_slow > 0:
                    sell_open_score_sma_dc_fast_slow -= 1
                if sell_open_score_env_touch > 0:
                    sell_open_score_env_touch -= 1
                if sell_open_score_env_penalty > 0:
                    sell_open_score_env_penalty -= 1

            # ポジション統計の取得
            if sell_current_position:

                # 最大含み益
                if candle.lows[-1] < sell_current_position.open_price:
                    if sell_current_position.open_price - candle.lows[-1] > sell_current_position.max_profit:
                        sell_current_position.max_profit = \
                            sell_current_position.open_price - candle.lows[-1]
                # 最大含み損
                if candle.highs[-1] > sell_current_position.open_price:
                    if sell_current_position.open_price - candle.highs[-1] < sell_current_position.max_loss:
                        sell_current_position.max_loss = \
                            sell_current_position.open_price - candle.highs[-1]

                # ホールド期間
                if candle.times[-1] != sell_current_position.open_time \
                        and candle.times[-1] > evaluated_til:
                    sell_current_position.hold_period += 1

            # クローズ(label="標準偏差順張り")
            if sell_current_position \
                    and sell_current_position.open_label == "標準偏差順張り":

                # 利確トリガー(BB: -1σ上抜け) ⇒ 足の確定を待つ
                if sell_current_position and sell_current_position.hold_period >= 4:
                    if candle.closes[-2] > bb_m1.prices[-2]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = candle.opens[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", candle.opens[-1], "-1σ上抜け")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 利確トリガー(BB: -3σタッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 4:
                    if candle.closes[-1] < bb_m3.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = bb_m3.prices[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", bb_m3.prices[-1], "-3σタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 1:
                    if candle.closes[-1] > sma_middle.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = sma_middle.prices[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", sma_middle.prices[-1], "sma_middleタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

            # クローズ(label="下げ基調のデッドクロス")
            if sell_current_position \
                    and sell_current_position.open_label == "調整局面のデッドクロス":

                # 利確トリガー(BB: -1σ上抜け) ⇒ 足の確定を待つ
                if sell_current_position and sell_current_position.hold_period >= 1:
                    if candle.closes[-2] > bb_m1.prices[-2]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = candle.opens[-1]
                        # スコアの更新
                        if sell_current_position.hold_period <= 10:
                            sell_open_score_bb_penalty = 10 - sell_current_position.hold_period
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", candle.opens[-1], "-1σ上抜け")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 利確トリガー(BB: -3σタッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 1:
                    if candle.closes[-1] < bb_m3.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = bb_m3.prices[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", bb_m3.prices[-1], "-3σタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 1:
                    if candle.closes[-1] > sma_middle.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = sma_middle.prices[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", sma_middle.prices[-1], "sma_middleタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

            # クローズ(label="エンベロープ逆張り")
            if sell_current_position \
                    and sell_current_position.open_label == "エンベロープ逆張り":

                # 利確トリガー(ENV: env_mdタッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 1:
                    if candle.lows[-1] < env_md.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", candle.closes[-1], "env_mdタッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 損切りトリガー(ENV: 建値割込み) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 4:
                    if candle.highs[-1] > sell_current_position.open_price:
                        # チャートの更新
                        sell_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", candle.closes[-1], "同値撤退")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # スコアの更新
                        sell_open_score_env_penalty = 30
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

                # 損切りトリガー(ENV: プラス乖離2タッチ) ⇒ 足の確定を待たない
                if sell_current_position and sell_current_position.hold_period >= 0:
                    if candle.highs[-1] > env_u2.prices[-1]:
                        # チャートの更新
                        sell_signal_close.prices[-1] = candle.closes[-1]
                        # ポジションの更新
                        sell_current_position.close(candle.times[-1], "buy", candle.closes[-1], "プラス乖離2タッチ")
                        # Slackの更新
                        if self._trade_mode == "practice":
                            chart.save_as_png("report/chart.png")
                            self._slack.send_position(sell_current_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                        # スコアの更新
                        sell_open_score_env_penalty = 30
                        # ポジション履歴の更新
                        sell_positions.append(sell_current_position)
                        sell_current_position = None

            # トレードサマリ(買いストラテジー)
            buy_balance = int(sum(list(map(lambda x: x.profit, buy_positions))))
            buy_count = len(buy_positions)
            buy_max_profit = int(max(list(map(lambda x: x.profit, buy_positions)), default=0))
            buy_max_drawdown = int(min(list(map(lambda x: x.profit, buy_positions)), default=0))
            summary_buy = "time:{}, buy_balance:{}, buy_count:{}, max_profit:{}, max_drawdown:{}".format(
                candle.times[0], buy_balance, buy_count, buy_max_profit, buy_max_drawdown
            )

            # トレードサマリ(売りストラテジー)
            sell_balance = int(sum(list(map(lambda x: x.profit, sell_positions))))
            sell_count = len(sell_positions)
            sell_max_profit = int(max(list(map(lambda x: x.profit, sell_positions)), default=0))
            sell_max_drawdown = int(min(list(map(lambda x: x.profit, sell_positions)), default=0))
            summary_sell = "time:{}, sell_balance:{}, sell_count:{}, max_profit:{}, max_drawdown:{}".format(
                candle.times[0], sell_balance, sell_count, sell_max_profit, sell_max_drawdown
            )

            # トレードサマリ(合計)
            summary_total = "time:{}, total_balance:{}, buy_strategy:{}, sell_strategy:{}".format(
                candle.times[0], buy_balance + sell_balance, buy_balance, sell_balance
            )

            print("------------------------------")
            print(summary_buy)
            print(summary_sell)
            print(summary_total)
            print("------------------------------")
            rank = sorted(buy_positions, key=lambda x: x.profit)
            for item in rank:
                print(item.to_str())
            print("------------------------------")
            rank = sorted(sell_positions, key=lambda x: x.profit)
            for item in rank:
                print(item.to_str())
            print("==============================")

            evaluated_til = candle.times[-1]

            feeder.go_next()
            chart.refresh()


if __name__ == "__main__":

    # Slack
    slack_token = ""
    slack_channel = ""
    slack_username = ""
    # Slack通知 : OFF
    # slack = SlackMessenger(slack_token, slack_channel, slack_username, True)
    # Slack通知 : ON
    slack = SlackMessenger(slack_token, slack_channel, slack_username, False)

    balance_fix = 0

    terminal = TradeTerminal("btc_jpy", "5m", "practice", datetime(2019, 3, 1), datetime(2019, 6, 30), slack, balance_fix)
    terminal.start()
