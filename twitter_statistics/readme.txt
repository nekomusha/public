■必要環境

このプログラムを動かすには、Pythonの実行環境の他に以下が必要です。

・IPA辞書(UTF-8)
・上記辞書が読み込めるMeCabライブラリ
・Gwibberが動作し、保存したデータベース(SQLite)
・SQLAlchemy Pythonパッケージ
(・データ格納先にMySQLを使用する場合はMySQL Serverとそのクライアント用Pythonバインディング)

上記は環境はUbuntu 10.10デスクトップ版なら、以下のパッケージをaptで
インストールが必要ということです。

・python-sqlalchemy
・mecab-ipadic-utf-8
・python-mecab
(・データ格納先にMySQLを使用する場合はmysql-server(別マシンでも可))
(・データ格納先にMySQLを使用する場合はpython-mysqldb)

ただしGwibberでツイートを読んでいないと集計対象データが0になります。

■できること

Gwibberで取り込んだ日本語ツイートから、発言頻度の多い人順に上位10名まで
その人の特徴的な単語を5つまで標準出力に表示します。

一度動作させるとホームディレクトリのmorph.sqliteにデータベースを作成し
そこまでの解析結果を保存します。これにより次に起動したときはより新しい
ツイートのみ処理するのですが、不要になったらこのファイルも消してください。

■環境インストール後の準備

(A)SQLiteを使う場合
特にすることはありません。

(B)MySQLを使う場合
事前にデータベースを用意する必要があります。
~/.config/twitter_statistics/config.iniを編集して(実行すると
デフォルト値で作成されます)、SQLAlchemyのDB接続用文字列を用意した
MySQLへの接続用に書き換えてください。以下は1例です。

[Statistics]
DatabaseURI = mysql+mysqldb://root@localhost/morph?charset=utf8&use_unicode=1

この内容である場合、localhostにあるMySQLサーバに繋ぎに行きます。
使用されるデータベースはmorphです。morphは以下のように作られていると
仮定されます。

CREATE DATABASE `morph` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin

■使い方

main.pyを実行するだけです。実行属性を付けてそのまま実行するか、
python main.pyで実行してください。