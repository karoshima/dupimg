#!/bin/bash

echo "=== クリーンアップを開始します ==="

# Python 仮想環境の無効化
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Python 仮想環境を無効化中..."
    deactivate
    echo "Python 仮想環境を無効化しました。"
else
    echo "Python 仮想環境は有効化されていません。"
fi

# Python 仮想環境の削除
if [ -d "venv" ]; then
    echo "Python 仮想環境を削除中..."
    rm -rf venv
    echo "Python 仮想環境を削除しました。"
else
    echo "Python 仮想環境は存在しません。"
fi

# Node.js パッケージの削除
if [ -d "node_modules" ]; then
    echo "Node.js パッケージを削除中..."
    rm -rf node_modules
    echo "Node.js パッケージを削除しました。"
else
    echo "Node.js パッケージは存在しません。"
fi

# TypeScript コンパイル結果の削除
if [ -d "static/js" ]; then
    echo "TypeScript コンパイル結果を削除中..."
    rm -rf static/js
    echo "TypeScript コンパイル結果を削除しました。"
else
    echo "TypeScript コンパイル結果は存在しません。"
fi

echo "=== クリーンアップが完了しました ==="
