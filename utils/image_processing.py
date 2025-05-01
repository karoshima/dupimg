import threading
import time

# グローバル変数で進捗状況を管理
progress_data = {
    "time": "",
    "progress": 0,
    "status": "未開始",
    "message": "",
    "steps": [
        {"name": "画像ファイルの一覧作成", "progress": 0, "status": "未開始"},
        {"name": "画像ファイルのハッシュ計算", "progress": 0, "status": "未開始"},
        {"name": "類似画像のグルーピング", "progress": 0, "status": "未開始"},
    ],
}

def get_progress():
    """
    現在の進捗状況を返す。
    """
    global progress_data
    return progress_data

def background_image_processing():
    """
    画像探索処理をバックグラウンドで実行する。
    """
    global progress_data

    # ステップ 1: 画像ファイルの一覧作成
    progress_data["status"] = "一覧作成中"
    progress_data["message"] = "画像ファイルの一覧を作成しています..."
    progress_data["steps"][0]["status"] = "進行中"
    for i in range(1, 6):  # ダミー処理
        time.sleep(1)
        progress_data["steps"][0]["progress"] = i * 20
    progress_data["steps"][0]["status"] = "完了"

    # ステップ 2: 画像ファイルのハッシュ計算
    progress_data["status"] = "ハッシュ計算中"
    progress_data["message"] = "画像ファイルのハッシュを計算しています..."
    progress_data["steps"][1]["status"] = "進行中"
    for i in range(1, 11):  # ダミー処理
        time.sleep(1)
        progress_data["steps"][1]["progress"] = i * 10
    progress_data["steps"][1]["status"] = "完了"

    # ステップ 3: 類似画像のグルーピング
    progress_data["status"] = "グルーピング中"
    progress_data["message"] = "類似画像をグルーピングしています..."
    progress_data["steps"][2]["status"] = "進行中"
    for i in range(1, 11):  # ダミー処理
        time.sleep(1)
        progress_data["steps"][2]["progress"] = i * 10
    progress_data["steps"][2]["status"] = "完了"

    # 全体の進捗を完了に設定
    progress_data["progress"] = 100
    progress_data["status"] = "完了"
    progress_data["message"] = "画像探索処理が完了しました。"

def start_background_processing():
    """
    バックグラウンドで画像探索処理を開始する。
    """
    thread = threading.Thread(target=background_image_processing)
    thread.start()
