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

# .gitignore に記載したディレクトリ/ファイルの削除
shopt -s globstar
echo ".gitignore に記載したディレクトリ/ファイルを削除中..."
[ -f .gitignore ] && rm -rf $(git check-ignore **/*)

echo "=== クリーンアップが完了しました ==="
