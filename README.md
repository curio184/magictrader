MagicTrader
=============

MagicTraderとは、zaif-exchangeでシステムトレードを行うためのフレームワークです。
ローソク足の取得、チャートの描画、そしてバックテスト・フォワードテストの機能を備えます。
各種テストでは、シグナルをチャートにプロットすることができるため、
チャートを確認しならアルゴリズムを検証することができます。

環境構築について (Windows編)
=============

本プロジェクトを実行するために必要である
Python3.5.2の仮想環境を構築する。

### Pythonバージョンの確認

```
$ python -V
Python 3.5.2
```

### Python仮想環境の作成

```
$ cd /d d:\
$ cd d:\Source\MagicTrader\.venv
$ python -m venv py352
$ d:\Source\MagicTrader\.venv\py352\Scripts\activate
$ python -V
Python 3.5.2
```

### Pythonライブラリのインストール

```
$ python -m pip install --upgrade pip
$ python -m pip install pylint
$ python -m pip install autopep8
$ python -m pip install rope
$ python -m pip install ptvsd
$ python -m pip install D:\Source\MagicTrader\setup\TA_Lib-0.4.10-cp35-cp35m-win_amd64.whl
$ python -m pip install matplotlib
$ python -m pip install mpl_finance
$ python -m pip install SQLAlchemy
$ python -m pip install numpy
$ python -m pip install zaifer
```
