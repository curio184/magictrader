from datetime import datetime, timedelta

from magictrader.candle import Candle, CandleFeeder
from magictrader.chart import Chart, ChartWindow
from magictrader.const import ModeBAND, Period
from magictrader.indicator import ADX, BBANDS, ENVELOPE, RSI, SMA, STDDEV, ATRBAND
from magictrader.position import Position, PositionRepository
from magictrader.terminal import TradeTerminal


class ScoreBoard:

    def __init__(self):
        self.signal_dip_ready = 999
        self.signal_rip_ready = 999
        self.signal_bband_break_p1 = 0
        self.signal_bband_break_m1 = 0
        self.signal_stddev_bull = 0
        self.signal_stddev_bear = 0
        self.signal_stddev_jumpup = 0
        self.signal_stddev_peakout = 0
        self.signal_adx_bull = 0
        self.signal_adx_bear = 0
        self.signal_adx_jumpup = 0
        self.signal_adx_peakout = 0
        self.signal_atrb_break = 0
        self.signal_sma_gc_fast_middle = 0
        self.signal_sma_gc_fast_slow = 0
        self.signal_sma_dc_fast_middle = 0
        self.signal_sma_dc_fast_slow = 0
        self.signal_env_touch_p1 = 0
        self.signal_env_touch_m1 = 0
        self.signal_bull_trend = 0
        self.signal_bear_trend = 0
        self.penalty_long_on_follow_stddev = 0
        self.penalty_long_on_contrary_env = 0
        self.penalty_short_on_follow_stddev = 0
        self.penalty_short_on_contrary_env = 0

    def decay(self):
        if self.signal_dip_ready > 0:
            self.signal_dip_ready -= 1
        if self.signal_rip_ready > 0:
            self.signal_rip_ready -= 1
        if self.signal_bband_break_p1 > 0:
            self.signal_bband_break_p1 -= 1
        if self.signal_bband_break_m1 > 0:
            self.signal_bband_break_m1 -= 1
        if self.signal_stddev_bull > 0:
            self.signal_stddev_bull -= 1
        if self.signal_stddev_bear > 0:
            self.signal_stddev_bear -= 1
        if self.signal_stddev_jumpup > 0:
            self.signal_stddev_jumpup -= 1
        if self.signal_stddev_peakout > 0:
            self.signal_stddev_peakout -= 1
        if self.signal_adx_bull > 0:
            self.signal_adx_bull -= 1
        if self.signal_adx_bear > 0:
            self.signal_adx_bear -= 1
        if self.signal_adx_jumpup > 0:
            self.signal_adx_jumpup -= 1
        if self.signal_adx_peakout > 0:
            self.signal_adx_peakout -= 1
        if self.signal_atrb_break > 0:
            self.signal_atrb_break -= 1
        if self.signal_sma_gc_fast_middle > 0:
            self.signal_sma_gc_fast_middle -= 1
        if self.signal_sma_gc_fast_slow > 0:
            self.signal_sma_gc_fast_slow -= 1
        if self.signal_sma_dc_fast_middle > 0:
            self.signal_sma_dc_fast_middle -= 1
        if self.signal_sma_dc_fast_slow > 0:
            self.signal_sma_dc_fast_slow -= 1
        if self.signal_env_touch_p1 > 0:
            self.signal_env_touch_p1 -= 1
        if self.signal_env_touch_m1 > 0:
            self.signal_env_touch_m1 -= 1
        if self.signal_bull_trend > 0:
            self.signal_bull_trend -= 1
        if self.signal_bear_trend > 0:
            self.signal_bear_trend -= 1
        if self.penalty_long_on_follow_stddev > 0:
            self.penalty_long_on_follow_stddev -= 1
        if self.penalty_long_on_contrary_env > 0:
            self.penalty_long_on_contrary_env -= 1
        if self.penalty_short_on_follow_stddev > 0:
            self.penalty_short_on_follow_stddev -= 1
        if self.penalty_short_on_contrary_env > 0:
            self.penalty_short_on_contrary_env -= 1


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

        ##################################################
        # テクニカルインディケーターを作成する
        ##################################################

        # SMA
        sma_fast = SMA(feeder, 5, "sma_fast")
        sma_middle = SMA(feeder, 21, "sma_middle")
        sma_slow = SMA(feeder, 89, "sma_slow")

        # BBANDS
        bb_p3 = BBANDS(feeder, 21, 3, ModeBAND.UPPER, "bb_p3")
        bb_p2 = BBANDS(feeder, 21, 2, ModeBAND.UPPER, "bb_p2")
        bb_p1 = BBANDS(feeder, 21, 1, ModeBAND.UPPER, "bb_p1")
        bb_md = BBANDS(feeder, 21, 1, ModeBAND.MIDDLE, "bb_midle")
        bb_m1 = BBANDS(feeder, 21, 1, ModeBAND.LOWER, "bb_m1")
        bb_m2 = BBANDS(feeder, 21, 2, ModeBAND.LOWER, "bb_m2")
        bb_m3 = BBANDS(feeder, 21, 3, ModeBAND.LOWER, "bb_m3")

        # ADX
        adx_fast = ADX(feeder, 8, "adx_fast")
        adx_fast.style = {"linestyle": "solid", "color": "red", "linewidth": 1, "alpha": 1}
        adx_slow = ADX(feeder, 14, "adx_slow")
        adx_slow.style = {"linestyle": "solid", "color": "green", "linewidth": 1, "alpha": 1}

        # STDDEV
        stddev = STDDEV(feeder, 26, 1, "stddev")

        # ATRBAND
        atrb_u1 = ATRBAND(feeder, 49, 14, 2, ModeBAND.UPPER, "atrb_u1")
        atrb_u1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}
        atrb_l1 = ATRBAND(feeder, 49, 14, 2, ModeBAND.LOWER, "atrb_l1")
        atrb_l1.style = {"linestyle": "solid", "color": "orange", "linewidth": 1, "alpha": 1}

        # ENVELOPE
        dev_rate1 = 0.1
        dev_rate2 = 0.13
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

        ##################################################
        # チャートの画面構成を定義する
        ##################################################

        # チャートのメイン画面に表示するテクニカルインディケーターを登録する
        window_main.height_ratio = 3
        window_main.legend_visible = False
        window_main.indicators_left.extend(
            [sma_fast, sma_middle, sma_slow,
             bb_p3, bb_p2, bb_p1, bb_md, bb_m1, bb_m2, bb_m3,
             atrb_u1, atrb_l1,
             env_u2, env_u1, env_md, env_l1, env_l2]
        )

        # チャートのサブ画面に表示するテクニカルインディケーターを登録する
        window_sub = ChartWindow()
        window_sub.height_ratio = 1
        window_sub.indicators_left.extend([adx_fast, adx_slow])
        window_sub.indicators_right.append(stddev)

        # チャートにサブ画面を登録する
        chart.add_window(window_sub)

        ##################################################
        # on_tickイベントに受け渡すデータを格納する
        ##################################################

        # テクニカルインディケーター
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
        data_bag["atrb_u1"] = atrb_u1
        data_bag["atrb_l1"] = atrb_l1
        data_bag["adx_fast"] = adx_fast
        data_bag["adx_slow"] = adx_slow
        data_bag["stddev"] = stddev
        data_bag["env_u2"] = env_u2
        data_bag["env_u1"] = env_u1
        data_bag["env_md"] = env_md
        data_bag["env_l1"] = env_l1
        data_bag["env_l2"] = env_l2

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

        ##################################################
        # 受け渡されたデータを引き出す
        ##################################################

        # テクニカルインディケーター
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
        atrb_u1 = data_bag["atrb_u1"]
        atrb_l1 = data_bag["atrb_l1"]
        adx_fast = data_bag["adx_fast"]
        adx_slow = data_bag["adx_slow"]
        stddev = data_bag["stddev"]
        env_u2 = data_bag["env_u2"]
        env_u1 = data_bag["env_u1"]
        env_md = data_bag["env_md"]
        env_l1 = data_bag["env_l1"]
        env_l2 = data_bag["env_l2"]

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

        ##################################################
        # シグナルの検出
        ##################################################

        acceleration_rate = 0.7

        # BBAND: +1σ上抜け
        if candle.closes[-2] < bb_p1.prices[-2] \
                and candle.closes[-1] > bb_p1.prices[-1]:
            score.signal_bband_break_p1 = 5

        # BBAND: -1σ下抜け
        if candle.closes[-2] > bb_m1.prices[-2] \
                and candle.closes[-1] < bb_m1.prices[-1]:
            score.signal_bband_break_m1 = 5

        # SMA: ゴールデンクロス fast/middle
        if sma_fast.prices[-3] < sma_middle.prices[-3] \
                and sma_fast.prices[-2] > sma_middle.prices[-2]:
            score.signal_sma_gc_fast_middle = 5

        # SMA: ゴールデンクロス fast/slow
        if sma_fast.prices[-3] < sma_slow.prices[-3] \
                and sma_fast.prices[-2] > sma_slow.prices[-2]:
            score.signal_sma_gc_fast_slow = 5

        # SMA: デッドクロス fast/middle
        if sma_fast.prices[-3] > sma_middle.prices[-3] \
                and sma_fast.prices[-2] < sma_middle.prices[-2]:
            score.signal_sma_dc_fast_middle = 5

        # SMA: デッドクロス fast/slow
        if sma_fast.prices[-3] > sma_slow.prices[-3] \
                and sma_fast.prices[-2] < sma_slow.prices[-2]:
            score.signal_sma_dc_fast_slow = 5

        # STDDEV: 上昇加速傾向
        if stddev.prices[-2] > stddev.prices[-3] \
                and stddev.prices[-1] > stddev.prices[-2] \
                and (stddev.prices[-1] - stddev.prices[-2]) > (stddev.prices[-2] - stddev.prices[-3]) * acceleration_rate:
            score.signal_stddev_bull = 3

        # STDDEV: 下降加速傾向
        if stddev.prices[-2] < stddev.prices[-3] \
                and stddev.prices[-1] < stddev.prices[-2] \
                and (stddev.prices[-2] - stddev.prices[-1]) > (stddev.prices[-3] - stddev.prices[-2]) * acceleration_rate:
            score.signal_stddev_bear = 3

        # STDDEV: ジャンプアップ
        if stddev.prices[-1] >= min(stddev.prices[-3:-1]):
            score.signal_stddev_jumpup = 3

        # STDDEV: ピークアウト
        if stddev.prices[-1] <= max(stddev.prices[-5:-1]):
            score.signal_stddev_peakout = 5

        # ADX: 上昇加速傾向
        if adx_slow.prices[-2] > adx_slow.prices[-3] \
                and adx_slow.prices[-1] > adx_slow.prices[-2] \
                and (adx_slow.prices[-1] - adx_slow.prices[-2]) > (adx_slow.prices[-2] - adx_slow.prices[-3]) * acceleration_rate:
            score.signal_adx_bull = 3

        # ADX: 下降加速傾向
        if adx_slow.prices[-2] < adx_slow.prices[-3] \
                and adx_slow.prices[-1] < adx_slow.prices[-2] \
                and (adx_slow.prices[-2] - adx_slow.prices[-1]) > (adx_slow.prices[-3] - adx_slow.prices[-2]) * acceleration_rate:
            score.signal_adx_bear = 3

        # ADX: ジャンプアップ
        if adx_fast.prices[-1] >= min(adx_fast.prices[-3:-1]):
            score.signal_adx_jumpup = 3

        # ADX: ピークアウト
        if adx_fast.prices[-1] <= max(adx_fast.prices[-5:-1]):
            score.signal_adx_peakout = 3

        # ATRBAND: ブレイク
        if candle.highs[-1] >= atrb_u1.prices[-1] \
                or candle.lows[-1] <= atrb_l1.prices[-1]:
            score.signal_atrb_break = 5

        # ENVELOPE: プラス乖離1タッチ
        if candle.highs[-1] > env_u1.prices[-1] \
                and candle.highs[-1] < env_u2.prices[-1]:
            score.signal_env_touch_p1 = 1

        # ENVELOPE: マイナス乖離1タッチ
        if candle.lows[-1] < env_l1.prices[-1] \
                and candle.lows[-1] > env_l2.prices[-1]:
            score.signal_env_touch_m1 = 1

        # 押し目
        # score.signal_dip_ready

        # 戻り高値
        if candle.highs[-2] >= sma_middle.prices[-2] \
                or candle.highs[-2] >= sma_slow.prices[-2]:
            score.signal_rip_ready = 999

        ##################################################
        # 買いストラテジー
        ##################################################

        # エントリー：標準偏差順張り
        # 条件：BBBAND +1σ上抜け、BBAND +1σ上で推移
        # 条件：STDDEV, ADXが上昇加速傾向
        if not long_position:
            if score.penalty_long_on_follow_stddev == 0 \
                    and candle.closes[-1] > bb_p1.prices[-1] \
                    and score.signal_bband_break_p1 > 0 \
                    and (score.signal_adx_bull > 0 or score.signal_adx_jumpup > 0) \
                    and (score.signal_stddev_bull > 0 or score.signal_stddev_jumpup > 0):
                # ポジション
                long_position = position_repository.create_position()
                long_position.open(candle.times[-1], "buy", candle.closes[-1], 1, "標準偏差順張り")
                # シグナルスコア
                score.signal_bull_trend = 20

        # エントリー：エンベロープ逆張り
        # 条件：ENVELOPE マイナス乖離1タッチ
        # 条件：BB/ADX/STD: 売りトレンドが発生していない
        if not long_position:
            if score.penalty_long_on_contrary_env == 0 \
                    and score.signal_env_touch_m1 > 0 \
                    and not (score.signal_bband_break_m1 > 0
                             and score.signal_adx_bull > 0
                             and score.signal_stddev_bull > 0):
                # ポジション
                long_position = position_repository.create_position()
                long_position.open(candle.times[-1], "buy", candle.closes[-1], 1, "エンベロープ逆張り")

        # イグジット：標準偏差順張り
        if long_position \
                and long_position.open_comment == "標準偏差順張り":

            # 利確：BB+1σ下抜け
            if not long_position.is_closed and long_position.hold_period >= 4:
                if candle.closes[-2] < bb_p1.prices[-2]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "+1σ下抜け")
                    # ペナルティスコア
                    if long_position.hold_period <= 10:
                        score.penalty_long_on_follow_stddev = 10 - long_position.hold_period

            # 利確：標準偏差ピークアウト
            if not long_position.is_closed and long_position.hold_period >= 1:
                if score.signal_atrb_break <= score.signal_stddev_peakout \
                        and score.signal_atrb_break <= score.signal_adx_peakout \
                        and score.signal_atrb_break > 0 \
                        and score.signal_stddev_peakout > 0 \
                        and score.signal_adx_peakout > 0:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "標準偏差ピークアウト")
                    # ペナルティスコア
                    if long_position.hold_period <= 10:
                        score.penalty_long_on_follow_stddev = 10 - long_position.hold_period

            # 損切り：中期SMAタッチ
            if not long_position.is_closed and long_position.hold_period >= 1:
                if candle.closes[-1] < sma_middle.prices[-1]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "sma_middleタッチ")

        # イグジット：エンベロープ逆張り
        if long_position \
                and long_position.open_comment == "エンベロープ逆張り":

            # 利確：中期ENVELOPEタッチ
            if not long_position.is_closed and long_position.hold_period >= 1:
                if candle.highs[-1] > env_md.prices[-1]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "env_mdタッチ")

            # 損切り：建値割込み
            if not long_position.is_closed and long_position.hold_period >= 4:
                if candle.lows[-1] < long_position.open_price:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "同値撤退")
                    # ペナルティスコア
                    score.penalty_long_on_contrary_env = 30

            # 損切り：マイナス乖離2タッチ
            if not long_position.is_closed and long_position.hold_period >= 0:
                if candle.lows[-1] < env_l2.prices[-1]:
                    # ポジション
                    long_position.close(candle.times[-1], candle.closes[-1], "マイナス乖離2タッチ")
                    # ペナルティスコア
                    score.penalty_long_on_contrary_env = 30

        ##################################################
        # 売りストラテジー
        ##################################################

        # エントリー：標準偏差順張り
        # 条件：BBAND -1σ下抜け、BBAND -1σ下で推移
        # 条件：STDDEV, ADXが上昇加速傾向
        if not short_position:
            if score.penalty_short_on_follow_stddev == 0 \
                    and score.signal_rip_ready > 0 \
                    and candle.closes[-1] < bb_m1.prices[-1] \
                    and score.signal_bband_break_m1 > 0 \
                    and (score.signal_adx_bull > 0 or score.signal_adx_jumpup > 0) \
                    and (score.signal_stddev_bull > 0 or score.signal_stddev_jumpup > 0):
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "標準偏差順張り")
                # シグナルスコア
                score.signal_rip_ready = 0

        # エントリー：エンベロープ逆張り
        # 条件：ENVELOPE プラス乖離1タッチ
        # 条件：BB/ADX/STD: 買いトレンドが発生していない
        if not short_position:
            if score.penalty_short_on_contrary_env == 0 \
                and score.signal_env_touch_p1 > 0 \
                and not (score.signal_bband_break_p1 > 0
                         and score.signal_adx_bull > 0
                         and score.signal_stddev_bull > 0):
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "エンベロープ逆張り")
                # シグナルスコア
                score.signal_rip_ready = 0

        # エントリー：調整局面のデッドクロス
        # 条件：BBBAND -1σ下が継続中
        # 条件：すべてのトリガーが発動中
        if not short_position:
            if score.signal_rip_ready > 0 \
                    and candle.closes[-1] < bb_m1.prices[-1] \
                    and score.signal_bband_break_m1 > 0 \
                    and score.signal_adx_bear > 0 \
                    and score.signal_stddev_bear > 0 \
                    and score.signal_sma_dc_fast_middle > 0 \
                    and score.signal_sma_dc_fast_slow > 0:
                # ポジション
                short_position = position_repository.create_position()
                short_position.open(candle.times[-1], "sell", candle.closes[-1], 1, "調整局面のデッドクロス")
                # シグナルスコア
                score.signal_rip_ready = 0

        # イグジット：標準偏差順張り
        if short_position \
                and short_position.open_comment == "標準偏差順張り":

            # 利確：BBAND -1σ上抜け
            if not short_position.is_closed and short_position.hold_period >= 4:
                if candle.closes[-2] > bb_m1.prices[-2]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "-1σ上抜け")
                    # ペナルティスコア
                    if short_position.hold_period <= 10:
                        score.penalty_short_on_follow_stddev = 10 - short_position.hold_period

            # 利確：標準偏差ピークアウト
            if not short_position.is_closed and short_position.hold_period >= 1:
                if score.signal_atrb_break <= score.signal_stddev_peakout \
                        and score.signal_atrb_break <= score.signal_adx_peakout \
                        and score.signal_atrb_break > 0 \
                        and score.signal_stddev_peakout > 0 \
                        and score.signal_adx_peakout > 0:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "標準偏差ピークアウト")
                    # ペナルティスコア
                    if short_position.hold_period <= 10:
                        score.penalty_short_on_follow_stddev = 10 - short_position.hold_period

            # 利確：BBAND -3σタッチ
            if not short_position.is_closed and short_position.hold_period >= 4:
                if candle.closes[-1] < bb_m3.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "-3σタッチ")

            # 損切り：SMA 中期タッチ
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-1] > sma_middle.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "sma_middleタッチ")

        # イグジット：調整局面のデッドクロス
        if short_position \
                and short_position.open_comment == "調整局面のデッドクロス":

            # 利確：BBAND -1σ上抜け
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-2] > bb_m1.prices[-2]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "-1σ上抜け")
                    # ペナルティスコア
                    if short_position.hold_period <= 10:
                        score.penalty_short_on_follow_stddev = 10 - short_position.hold_period

            # 利確：BBAND -3σタッチ
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-1] < bb_m3.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "-3σタッチ")

            # 損切り：SMA 中期タッチ
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.closes[-1] > sma_middle.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "sma_middleタッチ")

        # イグジット：エンベロープ逆張り
        if short_position \
                and short_position.open_comment == "エンベロープ逆張り":

            # 利確：ENVELOPE 中期タッチ
            if not short_position.is_closed and short_position.hold_period >= 1:
                if candle.lows[-1] < env_md.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "env_mdタッチ")

            # 損切り：建値割込み
            if not short_position.is_closed and short_position.hold_period >= 4:
                if candle.highs[-1] > short_position.open_price:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "同値撤退")
                    # ペナルティスコア
                    score.penalty_short_on_contrary_env = 30

            # 損切り：ENVELOPE プラス乖離2タッチ
            if not short_position.is_closed and short_position.hold_period >= 0:
                if candle.highs[-1] > env_u2.prices[-1]:
                    # ポジション
                    short_position.close(candle.times[-1], candle.closes[-1], "プラス乖離2タッチ")
                    # ペナルティスコア
                    score.penalty_short_on_contrary_env = 30

        # シグナル・ペナルティスコアを時間経過とともに減衰させる
        if is_newbar:
            score.decay()

    def _on_opening_position(self, position: Position, position_repository: PositionRepository) -> (float, float, bool):
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


if __name__ == "__main__":

    # 実践モードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "practice", terminal_name="break_stddev")
    # フォワードテストモードで実行します
    # mytrade = MyTradeTerminal("btc_jpy", "4h", "forwardtest", terminal_name="break_stddev")
    # バックテストモードで実行します
    mytrade = MyTradeTerminal("btc_jpy", "4h", "backtest", datetime(2019, 3, 1), datetime(2019, 6, 30), terminal_name="break_stddev")

    mytrade.run()
