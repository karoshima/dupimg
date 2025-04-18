#!/bin/bash

echo "=== プロジェクト初期設定を開始します ==="

# Python 仮想環境の作成と有効化
if [ ! -d "venv" ]; then
    echo "Python 仮想環境を作成中..."
    python3 -m venv venv
    echo "Python 仮想環境を作成しました。"
else
    echo "Python 仮想環境は既に存在します。"
fi

echo "Python 仮想環境を有効化します..."
source venv/bin/activate

# Python パッケージのインストール
if [ -f "requirements.txt" ]; then
    echo "Python パッケージをインストール中..."
    python3 -m pip install -r requirements.txt
else
    echo "requirements.txt が見つかりません。スキップします。"
fi

# Node.js パッケージのインストール
if [ -f "package.json" ]; then
    echo "Node.js パッケージをインストール中..."
    npm install
else
    echo "package.json が見つかりません。スキップします。"
fi

# TypeScript のコンパイル
if [ -d "static/ts" ]; then
    echo "TypeScript をコンパイル中..."
    npx tsc
    echo "TypeScript のコンパイルが完了しました。"
else
    echo "TypeScript ディレクトリが見つかりません。スキップします。"
fi

echo "=== 初期設定が完了しました ==="
