MagicTrader
=============
![](https://img.shields.io/apm/l/vim-mode.svg)
![](https://img.shields.io/badge/Python-after%20v3-red.svg)
[![](https://img.shields.io/pypi/v/magictrader.svg)](https://pypi.org/project/magictrader/)

MagicTraderとは、zaif-exchangeでシステムトレードを行うためのフレームワークです。  
ローソク足、テクニカルインディケーターの取得はもちろん、  
チャートの表示や、バックテスト・フォワードテストの機能を備えます。  
各種テストでは、シグナルをチャートにプロットすることができるため、  
チャートを確認しならアルゴリズムを検証することができます。  

セットアップ
=============

### 1. MagicTraderをインストールする

pipコマンドを実行し、MagicTraderをインストールしてください。  

```
$ pip install magictrader
```

### 2. TA-Libをインストールする

MagicTraderは「TA-Lib」のインストールを別途必要とします。  
下記の紹介記事等を参考に、各々の環境に応じてインストールしてください。

python3でTA-Libをインストールする方法をまとめてみた  
https://qiita.com/ConnieWild/items/cb50f36425a683c914d2

```
$ pip install TA_Lib-0.4.17-cp35-cp35m-win_amd64.whl
```

使い方
=============

MagicTraderは、まず、プロジェクトを新規作成し、  
プロジェクトにアルゴリズムを記述し、  
プロジェクトを実行するという手順で使用します。  

### 1. プロジェクトを新規作成する

MagicTradeをインストールすると、  
プロジェクトを新規作成するためのコマンド「create_tradeterminal」がインストールされます。  
下記コマンドを実行してプロジェクトを新規作成してください。  

```
$ create_tradeterminal
```

プロジェクトの作成に成功すると、下記のファイルが作成されます。

```
mytrade.py  # プロジェクト本体です。
mt.ini      # プロジェクトの設定ファイルです。
```

### 2. プロジェクトを実行する

mytrade.pyには、ゴールデンクロスでロングポジションを取るアルゴリズムがあらかじめ実装されています。  
デフォルトではバックテストモードに設定されているため、実際にポジションが取ることはありません。  
まずは試しに実行してみてください。チャートが表示されれば成功です。

```
$ python mytrade.py
```

