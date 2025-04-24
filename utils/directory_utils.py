import os
from flask import jsonify

# 許可されたディレクトリ
allowed_directories = []

def set_allowed_directories(directories):
    """
    指定されたディレクトリを絶対パスに変換して保持する関数
    :param directories: 処理対象のディレクトリのリスト
    """
    global allowed_directories
    allowed_directories = [os.path.abspath(directory) for directory in directories]

def list_subdirectories(base_path):
    """
    指定されたパスのサブディレクトリをリストアップする。
    :param base_path: 基準となるディレクトリパス
    :return: サブディレクトリのリストを含む JSON レスポンス
    """
    # 初期値 "/" が指定された場合は、許可されたディレクトリを返す
    if base_path == "":
        directories = [{"name": allowed_dir, "path": allowed_dir} for allowed_dir in allowed_directories]
        return jsonify({"status": "success", "directories": directories})

    # 指定されたパスが許可されたディレクトリ内にあるか確認
    abs_base_path = os.path.abspath(base_path)
    if not any(abs_base_path.startswith(allowed_dir) for allowed_dir in allowed_directories):
        return jsonify({"status": "error", "message": "指定されたパスは許可されていません。"}), 400

    # サブディレクトリをリストアップ
    try:
        directories = [
            {"name": name, "path": os.path.join(base_path, name)}
            for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))
        ]
        return jsonify({"status": "success", "directories": directories})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def is_directory_allowed(directory):
    """
    指定されたディレクトリが許可されたディレクトリ内にあるかを確認する。
    :param directory: 検証対象のディレクトリ
    :return: True (許可されている場合), False (許可されていない場合)
    """
    abs_directory = os.path.normpath(os.path.abspath(directory))
    return any(abs_directory.startswith(allowed_dir) for allowed_dir in allowed_directories)
