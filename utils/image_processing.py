import imagehash
import os
import threading
from datetime import datetime
from typing import List, Any, Dict
from PIL import Image

# グローバル変数で進捗状況を管理
progress_data: Dict[str, Any] = {
    "time": "",
    "progress": 0,
    "page": "/settings",
    "status": "未開始",
    "message": "",
    "steps": [
        {"name": "画像ファイルの一覧作成", "progress": 0, "status": "未開始"},
        {"name": "画像ファイルのハッシュ計算", "progress": 0, "status": "未開始"},
        {"name": "類似画像のグルーピング", "progress": 0, "status": "未開始"},
    ],
}

def get_progress() -> Dict[str, Any]:
    """
    現在の進捗状況を返す。
    """
    global progress_data
    progress_data["time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    return progress_data

class ImageFile:
    """
    画像ファイルに関する様々なを表すクラス。
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.size = os.path.getsize(path)
        img: Image.Image = None
        try:
            img = Image.open(path)
        except Exception as e:
            print(f"Error opening image {path}: {e}")
            self.disabled = True
            return
        try:
            self.hash = imagehash.phash(img)
        except Exception as e:
            print(f"Error calculating hash for image {path}: {e}")
            self.disabled = True
            return
        self.disabled = False
        self.date = None
        exif_data = img._getexif()
        if exif_data:
            date_str = exif_data.get(36867) or exif_data.get(306)
            if date_str:
                for fmt in [ "%Y:%m:%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                    try:
                        self.date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    print(f"Unsupported date format in {path}: {date_str}")
        if not self.date:
            self.date = datetime.fromtimestamp(os.path.getctime(path))
        self.inode = os.stat(path).st_ino

    def __repr__(self) -> str:
        return f"ImageFile(path={self.path}, hash_value={self.hash_value})"

def background_image_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    画像探索処理をバックグラウンドで実行する。
    """
    global progress_data

    # ステップ 1: 画像ファイルの一覧作成
    progress_data["page"] = "/progress"
    progress_data["steps"][0]["progress"] = '?'
    progress_data["status"] = "一覧作成中"
    progress_data["message"] = "画像ファイルの一覧を作成しています..."
    progress_data["steps"][0]["status"] = "進行中"
    image_files: List[str] = []
    for dir in directory:
        for root, _, files in os.walk(dir):
            if ".@__thumb" in root:
                continue
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_files.append(os.path.join(root, file))
                    progress_data["message"] = f"画像ファイルを {len(image_files)} 件見つけました..."
    progress_data["steps"][0]["progress"] = 100
    progress_data["steps"][0]["status"] = "完了"

    # ステップ 2: 画像ファイルのハッシュ計算
    progress_data["status"] = "ハッシュ計算中"
    progress_data["steps"][1]["status"] = "進行中"
    images: List[ImageFile] = []
    for index, file_path in enumerate(image_files):
        try:
            image = ImageFile(file_path)
            images.append(image)
            progress_data["steps"][1]["progress"] = ((index + 1) * 10000 // len(image_files)) / 100
            progress_data["message"] = f"ハッシュ計算中: {index + 1}/{len(image_files)}"
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")
    progress_data["steps"][1]["status"] = "完了"

    # ステップ 3: 類似画像のグルーピング
    progress_data["status"] = "グルーピング中"
    progress_data["steps"][2]["status"] = "進行中"
    group_list: List[List[ImageFile]] = []
    inode_map: Dict[int, ImageFile] = {}
    for index, img in enumerate(images):
        # 既にハードリンクされたファイルはスキップ
        if img.inode in inode_map:
            continue
        inode_map[img.inode] = img
        # 既存のグループに追加するか新規のグループを作るか判定する
        for group in group_list:
            if any(abs(img.hash - other.hash) == 0 for other in group):
                group.append(img)
                break
        else:
            group_list.append([img])
        progress_data["steps"][2]["progress"] = ((index + 1) * 10000 // len(images)) / 100
        progress_data["message"] = f"グルーピング中: {index + 1}/{len(images)}, グループ数: {len(group_list)}"
    progress_data["steps"][2]["progress"] = 100
    progress_data["steps"][2]["status"] = "完了"

    # 全体の進捗を完了に設定
    progress_data["progress"] = 100
    progress_data["page"] = "/results"
    progress_data["status"] = "完了"
    progress_data["message"] = "画像探索処理が完了しました。"

def start_background_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    バックグラウンドで画像探索処理を開始する。
    """
    thread = threading.Thread(target=background_image_processing, args=(directory, algorithm, similarity))
    thread.start()
