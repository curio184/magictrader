from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBBANDS, Period
from magictrader.indicator import ADX, BBANDS, ENVELOPE, RSI, SMA, STDDEV
from magictrader.terminal import TradeTerminal
from magictrader.trade import Position, PositionRepository


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

        # SMA
        sma_fast = SMA(feeder, 5, "sma_fast")
        sma_middle = SMA(feeder, 21, "sma_middle")
        sma_slow = SMA(feeder, 89, "sma_slow")

        # BBANDS
        bb_p3 = BBANDS(feeder, 21, 3, ModeBBANDS.UPPER, "bb_p3")
        bb_p2 = BBANDS(feeder, 21, 2, ModeBBANDS.UPPER, "bb_p2")
        bb_p1 = BBANDS(feeder, 21, 1, ModeBBANDS.UPPER, "bb_p1")
        bb_md = BBANDS(feeder, 21, 1, ModeBBANDS.MIDDLE, "bb_midle")
        bb_m1 = BBANDS(feeder, 21, 1, ModeBBANDS.LOWER, "bb_m1")
        bb_m2 = BBANDS(feeder, 21, 2, ModeBBANDS.LOWER, "bb_m2")
        bb_m3 = BBANDS(feeder, 21, 3, ModeBBANDS.LOWER, "bb_m3")

        # ADX
        adx_fast = ADX(feeder, 13, "adx_fast")
        adx_fast.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        adx_slow = ADX(feeder, 26, "adx_slow")
        adx_slow.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}

        # STDDEV
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ENVELOPE
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

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.legend_visible = False
        window_main.indicators_left.extend(
            [sma_fast, sma_middle, sma_slow,
             bb_p3, bb_p2, bb_p1, bb_md, bb_m1, bb_m2, bb_m3,
             env_u2, env_u1, env_md, env_l1, env_l2]
        )

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.extend([adx_fast, adx_slow])
        window_sub.indicators_right.append(stddev)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        # on_tickイベントに受け渡すデータを格納する
        data_bag["sma_fast"] = sma_fast
        data_bag["sma_middle"] = sma_middle
        data_bag["sma_slow"] = sma_slow
        data_bag["bb_p3"] = bb_p3
        data_bag["bb_p2"] = bb_p2
        data_bag["bb_p1"] = bb_p1
        data_bag["bb_md"] = bb_md
        data_bag["bb_m1"] = bb_m1
        data_bag["bb_m2"] = bb_m2
        data_bag["bb_m3"] = bb_m3
        data_bag["adx_fast"] = adx_fast
        data_bag["adx_slow"] = adx_slow
        data_bag["stddev"] = stddev
        data_bag["env_u2"] = env_u2
        data_bag["env_u1"] = env_u1
        data_bag["env_md"] = env_md
        data_bag["env_l1"] = env_l1
        data_bag["env_l2"] = env_l2

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
        sma_fast = data_bag["sma_fast"]
        sma_middle = data_bag["sma_middle"]
        sma_slow = data_bag["sma_slow"]
        bb_p3 = data_bag["bb_p3"]
        bb_p2 = data_bag["bb_p2"]
        bb_p1 = data_bag["bb_p1"]
        bb_md = data_bag["bb_md"]
        bb_m1 = data_bag["bb_m1"]
        bb_m2 = data_bag["bb_m2"]
        bb_m3 = data_bag["bb_m3"]
        adx_fast = data_bag["adx_fast"]
        adx_slow = data_bag["adx_slow"]
        stddev = data_bag["stddev"]
        env_u2 = data_bag["env_u2"]
        env_u1 = data_bag["env_u1"]
        env_md = data_bag["env_md"]
        env_l1 = data_bag["env_l1"]
        env_l2 = data_bag["env_l2"]

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

        # # 買いストラテジーのシグナルスコア
        # signal_bull_trend = 0
        # signal_bband_break_p1 = 0
        # signal_bband_break_m1 = 0
        # signal_stddev_bull = 0
        # signal_stddev_bear = 0
        # signal_adx_bull = 0
        # signal_adx_bear = 0
        # signal_sma_gc_fast_middle = 0
        # signal_sma_gc_fast_slow = 0
        # signal_env_touch_m1 = 0
        # penalty_long_on_follow_stddev = 0
        # penalty_long_on_contrary_env = 0

        # # 売りストラテジーのシグナルスコア
        # signal_rip_ready = False
        # short_signal_score_bear_trend = 0
        # short_signal_score_bband_break_p1 = 0
        # short_signal_score_bband_break_m1 = 0
        # signal_stddev_bull = 0
        # signal_stddev_bear = 0
        # signal_adx_bull = 0
        # signal_adx_bear = 0
        # signal_sma_dc_fast_middle = 0
        # signal_sma_dc_fast_slow = 0
        # signal_env_touch_p1 = 0
        # short_signal_score_bb_penalty = 0
        # short_signal_score_env_penalty = 0

        ##################################################
        # シグナルの検出
        ##################################################

        acceleration_rate = 0.7

        # BBAND: +1σ上抜け
        if candle.closes[-2] < bb_p1.prices[-2] \
                and candle.closes[-1] > bb_p1.prices[-1]:
            signal_bband_break_p1 = 5

        # BBAND: -1σ下抜け
        if candle.closes[-2] > bb_m1.prices[-2] \
                and candle.closes[-1] < bb_m1.prices[-1]:
            signal_bband_break_m1 = 5

        # SMA: ゴールデンクロス fast/middle
        if sma_fast.prices[-3] < sma_middle.prices[-3] \
                and sma_fast.prices[-2] > sma_middle.prices[-2]:
            signal_sma_gc_fast_middle = 5

        # SMA: ゴールデンクロス fast/slow
        if sma_fast.prices[-3] < sma_slow.prices[-3] \
                and sma_fast.prices[-2] > sma_slow.prices[-2]:
            signal_sma_gc_fast_slow = 5

        # SMA: デッドクロス fast/middle
        if sma_fast.prices[-3] > sma_middle.prices[-3] \
                and sma_fast.prices[-2] < sma_middle.prices[-2]:
            signal_sma_dc_fast_middle = 5

        # SMA: デッドクロス fast/slow
        if sma_fast.prices[-3] > sma_slow.prices[-3] \
                and sma_fast.prices[-2] < sma_slow.prices[-2]:
            signal_sma_dc_fast_slow = 5

        # STDDEV: 上昇加速傾向
        if stddev.prices[-2] > stddev.prices[-3] \
                and stddev.prices[-1] > stddev.prices[-2] \
                and (stddev.prices[-1] - stddev.prices[-2]) > (stddev.prices[-2] - stddev.prices[-3]) * acceleration_rate:
            signal_stddev_bull = 3

        # STDDEV: 下降加速傾向
        if stddev.prices[-2] < stddev.prices[-3] \
                and stddev.prices[-1] < stddev.prices[-2] \
                and (stddev.prices[-2] - stddev.prices[-1]) > (stddev.prices[-3] - stddev.prices[-2]) * acceleration_rate:
            signal_stddev_bear = 3

        # ADX: 上昇加速傾向
        if adx_slow.prices[-2] > adx_slow.prices[-3] \
                and adx_slow.prices[-1] > adx_slow.prices[-2] \
                and (adx_slow.prices[-1] - adx_slow.prices[-2]) > (adx_slow.prices[-2] - adx_slow.prices[-3]) * acceleration_rate:
            signal_adx_bull = 3

        # ADX: 下降加速傾向
        if adx_slow.prices[-2] < adx_slow.prices[-3] \
                and adx_slow.prices[-1] < adx_slow.prices[-2] \
                and (adx_slow.prices[-2] - adx_slow.prices[-1]) > (adx_slow.prices[-3] - adx_slow.prices[-2]) * acceleration_rate:
            signal_adx_bear = 3

        # ENVELOPE: プラス乖離1タッチ
        if candle.highs[-1] > env_u1.prices[-1] \
                and candle.highs[-1] < env_u2.prices[-1]:
            signal_env_touch_p1 = 1

        # ENVELOPE: マイナス乖離1タッチ
        if candle.lows[-1] < env_l1.prices[-1] \
                and candle.lows[-1] > env_l2.prices[-1]:
            signal_env_touch_m1 = 1

        # 押し目
        # signal_dip_ready

        # 戻り高値
        if candle.highs[-2] >= sma_middle.prices[-2] \
                or candle.highs[-2] >= sma_slow.prices[-2]:
            signal_rip_ready = True

        ##################################################
        # 買いストラテジー
        ##################################################

        # エントリー：標準偏差順張り
        # 条件：BB+1σを上抜けし、BB+1σ上で推移
        # 条件：STDDEV, ADXが上昇加速傾向
        if not long_position:
            if penalty_long_on_follow_stddev == 0 \
                    and candle.closes[-1] > bb_p1.prices[-1] \
                    and signal_bband_break_p1 > 0 \
                    and signal_adx_bull > 0 \
                    and signal_stddev_bull > 0:
                # ポジションオープン
                position = position_repository.create_position()
                position.open(candle.times[-1], "buy", candle.closes[-1], 1, "標準偏差順張り")
                # 複合シグナルの検出
                signal_bull_trend = 20

        # エントリー：エンベロープ逆張り
        # 条件：ENV: マイナス乖離1にタッチ
        # 条件：BB/ADX/STD: 売りトレンドが発生していない
        if not long_position:
            if penalty_long_on_contrary_env == 0 \
                    and signal_env_touch_m1 > 0 \
                    and not (signal_bband_break_m1 > 0
                             and signal_adx_bull > 0
                             and signal_stddev_bull > 0):
                # ポジションオープン
                position = position_repository.create_position()
                position.open(candle.times[-1], "buy", candle.closes[-1], 1, "エンベロープ逆張り")

        # ポジション統計の取得
        if long_position:

            # 最大含み益
            if candle.highs[-1] > long_position.open_price:
                if candle.highs[-1] - long_position.open_price > long_position.max_profit:
                    long_position.max_profit = \
                        candle.highs[-1] - long_position.open_price

            # 最大含み損
            if candle.lows[-1] < long_position.open_price:
                if candle.lows[-1] - long_position.open_price < long_position.max_loss:
                    long_position.max_loss = \
                        candle.lows[-1] - long_position.open_price

            # ホールド期間
            if candle.times[-1] != long_position.open_time \
                    and candle.times[-1] > evaluated_til:
                long_position.hold_period += 1

        # イグジット：標準偏差順張り
        if long_position \
                and long_position.open_comment == "標準偏差順張り":

            self._get_position_hold_period(
                long_position.open_time, candle.close_time[-1]
            )

            # 利確トリガー(BB: +1σ下抜け) ⇒ 足の確定を待つ
            if long_position and long_position.hold_period >= 4:
                if candle.closes[-2] < bb_p1.prices[-2]:
                    # ポジションの更新
                    long_position.close(candle.times[-1], "sell", candle.opens[-1], "+1σ下抜け")
                    # スコアの更新
                    if long_position.hold_period <= 10:
                        penalty_long_on_follow_stddev = 10 - long_position.hold_period

            # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
            if long_position and long_position.hold_period >= 1:
                if candle.closes[-1] < sma_middle.prices[-1]:

                    # ポジションクローズ
                    long_position.close(candle.times[-1], "sell", sma_middle.prices[-1], "sma_middleタッチ")

        # クローズ(label="エンベロープ逆張り")
        if long_position \
                and long_position.open_comment == "エンベロープ逆張り":

            # 利確トリガー(ENV: env_mdタッチ) ⇒ 足の確定を待たない
            if long_position and long_position.hold_period >= 1:
                if candle.highs[-1] > env_md.prices[-1]:
                    # ポジションの更新
                    long_position.close(candle.times[-1], "sell", candle.closes[-1], "env_mdタッチ")

            # 損切りトリガー(ENV: 建値割込み) ⇒ 足の確定を待たない
            if long_position and long_position.hold_period >= 4:
                if candle.lows[-1] < long_position.open_price:
                    # ポジションの更新
                    long_position.close(candle.times[-1], "sell", candle.closes[-1], "同値撤退")
                    # スコアの更新
                    penalty_long_on_contrary_env = 30

            # 損切りトリガー(ENV: マイナス乖離2タッチ) ⇒ 足の確定を待たない
            if long_position and long_position.hold_period >= 0:
                if candle.lows[-1] < env_l2.prices[-1]:
                    # ポジションの更新
                    long_position.close(candle.times[-1], "sell", candle.closes[-1], "マイナス乖離2タッチ")
                    # スコアの更新
                    penalty_long_on_contrary_env = 30

        ##################################################
        # 売りストラテジー
        ##################################################

        # 調整下げに反応するためのフィルタ
        # フィルタ(BB: -1σ下が継続中)
        # フィルタ(すべてのトリガーが発動中)
        if not short_position:
            if signal_rip_ready \
                    and candle.closes[-1] < bb_m1.prices[-1] \
                    and short_signal_score_bband_break_m1 > 0 \
                    and signal_adx_bear > 0 \
                    and signal_stddev_bear > 0 \
                    and signal_sma_dc_fast_middle > 0 \
                    and signal_sma_dc_fast_slow > 0:
                # ポジションの更新
                short_position = Position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], "調整局面のデッドクロス")
                # スコアの更新
                signal_rip_ready = False
                short_signal_score_bband_break_p1 = 0
                short_signal_score_bband_break_m1 = 0
                signal_stddev_bull = 0
                signal_stddev_bear = 0
                signal_adx_bull = 0
                signal_adx_bear = 0
                signal_sma_dc_fast_middle = 0
                signal_sma_dc_fast_slow = 0
                signal_env_touch_p1 = 0

        # 標準偏差順張りに反応するためのフィルタ
        # フィルタ(BB: -1σ下が継続中)
        # フィルタ(ADX: 上昇加速傾向)
        if not short_position:
            if signal_rip_ready \
                    and candle.closes[-1] < bb_m1.prices[-1] \
                    and short_signal_score_bband_break_m1 > 0 \
                    and signal_adx_bull > 0 \
                    and signal_stddev_bull > 0 \
                    and short_signal_score_bb_penalty == 0:
                # チャートの更新
                sell_signal_open.prices[-1] = candle.closes[-1]
                # Slackの更新
                if self._trade_mode == "practice":
                    chart.save_as_png("report/chart.png")
                    self._slack.send_position(short_position, buy_positions + sell_positions, self._balance_fix, "report/chart.png")
                # スコアの更新
                signal_rip_ready = False
                short_signal_score_bear_trend = 20
                short_signal_score_bband_break_p1 = 0
                short_signal_score_bband_break_m1 = 0
                signal_stddev_bull = 0
                signal_stddev_bear = 0
                signal_adx_bull = 0
                signal_adx_bear = 0
                signal_sma_dc_fast_middle = 0
                signal_sma_dc_fast_slow = 0
                signal_env_touch_p1 = 0

        # エンベロープ逆張りに反応するためのフィルタ
        # フィルタ(ENV: マイナス乖離1にタッチ)
        # フィルタ(BB/ADX/STD: 買いトレンドが発生していない)
        if not short_position:
            if signal_env_touch_p1 > 0 \
                and short_signal_score_env_penalty == 0 \
                and not (short_signal_score_bband_break_p1 > 0
                         and signal_adx_bull > 0
                         and signal_stddev_bull > 0):
                # ポジションの更新
                short_position = Position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], "エンベロープ逆張り")
                # スコアの更新
                signal_rip_ready = False
                short_signal_score_bband_break_p1 = 0
                short_signal_score_bband_break_m1 = 0
                signal_stddev_bull = 0
                signal_stddev_bear = 0
                signal_adx_bull = 0
                signal_adx_bear = 0
                signal_sma_dc_fast_middle = 0
                signal_sma_dc_fast_slow = 0
                signal_env_touch_p1 = 0

        # ポジション統計の取得
        if short_position:

            # 最大含み益
            if candle.lows[-1] < short_position.open_price:
                if short_position.open_price - candle.lows[-1] > short_position.max_profit:
                    short_position.max_profit = \
                        short_position.open_price - candle.lows[-1]
            # 最大含み損
            if candle.highs[-1] > short_position.open_price:
                if short_position.open_price - candle.highs[-1] < short_position.max_loss:
                    short_position.max_loss = \
                        short_position.open_price - candle.highs[-1]

            # ホールド期間
            if candle.times[-1] != short_position.open_time \
                    and candle.times[-1] > evaluated_til:
                short_position.hold_period += 1

        # クローズ(label="標準偏差順張り")
        if short_position \
                and short_position.open_comment == "標準偏差順張り":

            # 利確トリガー(BB: -1σ上抜け) ⇒ 足の確定を待つ
            if short_position and short_position.hold_period >= 4:
                if candle.closes[-2] > bb_m1.prices[-2]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", candle.opens[-1], "-1σ上抜け")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 利確トリガー(BB: -3σタッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 4:
                if candle.closes[-1] < bb_m3.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", bb_m3.prices[-1], "-3σタッチ")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 1:
                if candle.closes[-1] > sma_middle.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", sma_middle.prices[-1], "sma_middleタッチ")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

        # クローズ(label="下げ基調のデッドクロス")
        if short_position \
                and short_position.open_comment == "調整局面のデッドクロス":

            # 利確トリガー(BB: -1σ上抜け) ⇒ 足の確定を待つ
            if short_position and short_position.hold_period >= 1:
                if candle.closes[-2] > bb_m1.prices[-2]:
                    # スコアの更新
                    if short_position.hold_period <= 10:
                        short_signal_score_bb_penalty = 10 - short_position.hold_period
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", candle.opens[-1], "-1σ上抜け")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 利確トリガー(BB: -3σタッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 1:
                if candle.closes[-1] < bb_m3.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", bb_m3.prices[-1], "-3σタッチ")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 損切りトリガー(SMA: sma_middleタッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 1:
                if candle.closes[-1] > sma_middle.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", sma_middle.prices[-1], "sma_middleタッチ")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

        # クローズ(label="エンベロープ逆張り")
        if short_position \
                and short_position.open_comment == "エンベロープ逆張り":

            # 利確トリガー(ENV: env_mdタッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 1:
                if candle.lows[-1] < env_md.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", candle.closes[-1], "env_mdタッチ")
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 損切りトリガー(ENV: 建値割込み) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 4:
                if candle.highs[-1] > short_position.open_price:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", candle.closes[-1], "同値撤退")
                    # スコアの更新
                    short_signal_score_env_penalty = 30
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

            # 損切りトリガー(ENV: プラス乖離2タッチ) ⇒ 足の確定を待たない
            if short_position and short_position.hold_period >= 0:
                if candle.highs[-1] > env_u2.prices[-1]:
                    # ポジションの更新
                    short_position.close(candle.times[-1], "buy", candle.closes[-1], "プラス乖離2タッチ")
                    # スコアの更新
                    short_signal_score_env_penalty = 30
                    # ポジション履歴の更新
                    sell_positions.append(short_position)
                    short_position = None

        # 時間経過とともにシグナルを減衰させる
        if is_newbar:

            if signal_bull_trend > 0:
                signal_bull_trend -= 1
            if signal_bband_break_p1 > 0:
                signal_bband_break_p1 -= 1
            if signal_bband_break_m1 > 0:
                signal_bband_break_m1 -= 1
            if penalty_long_on_follow_stddev > 0:
                penalty_long_on_follow_stddev -= 1
            if signal_stddev_bull > 0:
                signal_stddev_bull -= 1
            if signal_stddev_bear > 0:
                signal_stddev_bear -= 1
            if signal_adx_bull > 0:
                signal_adx_bull -= 1
            if signal_adx_bear > 0:
                signal_adx_bear -= 1
            if signal_sma_gc_fast_middle > 0:
                signal_sma_gc_fast_middle -= 1
            if signal_sma_gc_fast_slow > 0:
                signal_sma_gc_fast_slow -= 1
            if signal_env_touch_m1 > 0:
                signal_env_touch_m1 -= 1
            if penalty_long_on_contrary_env > 0:
                penalty_long_on_contrary_env -= 1

            # うり
            if short_signal_score_bear_trend > 0:
                short_signal_score_bear_trend -= 1
            if short_signal_score_bband_break_p1 > 0:
                short_signal_score_bband_break_p1 -= 1
            if short_signal_score_bband_break_m1 > 0:
                short_signal_score_bband_break_m1 -= 1
            if short_signal_score_bb_penalty > 0:
                short_signal_score_bb_penalty -= 1
            if signal_stddev_bull > 0:
                signal_stddev_bull -= 1
            if signal_stddev_bear > 0:
                signal_stddev_bear -= 1
            if signal_adx_bull > 0:
                signal_adx_bull -= 1
            if signal_adx_bear > 0:
                signal_adx_bear -= 1
            if signal_sma_dc_fast_middle > 0:
                signal_sma_dc_fast_middle -= 1
            if signal_sma_dc_fast_slow > 0:
                signal_sma_dc_fast_slow -= 1
            if signal_env_touch_p1 > 0:
                signal_env_touch_p1 -= 1
            if short_signal_score_env_penalty > 0:
                short_signal_score_env_penalty -= 1

    def _on_opening_position(self, position: Position, position_repository: PositionRepository) -> (bool, float, float):
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
        (bool, float, float)
            1: ポジションを一部でも開くことに成功した場合Trueを返します。
            2: 実際の約定価格を返します。
            3: 実際の約定数量を返します。
        """
        return True, position.open_price, position.order_amount

    def _on_closing_position(self, position: Position, position_repository: PositionRepository) -> float:
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

    def _get_position_hold_period(self, open_time: datetime, close_time: datetime) -> int:
        """
        ポジションの保有期間を取得する
        """
        hold_period = 0
        datetime_cursor = open_time
        while datetime_cursor < close_time:
            hold_period += 1
            datetime_cursor += timedelta(minutes=Period.to_minutes(self._period))
        return hold_period


if __name__ == "__main__":

    # 実践モードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "5m", "practice")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "5m", "forwardtest")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "4h", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30))

    mytrade.run()
