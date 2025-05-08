import base64
from copy import deepcopy
import imagehash
import os
import threading
from datetime import datetime
from io import BytesIO
from typing import List, Any, Dict
from PIL import Image

class ImageFile:
    """
    画像ファイルに関する様々なを表すクラス。
    """
    def __init__(self, path: str) -> None:
        self.paths: List[str] = [path]
        self.size: int = os.path.getsize(path)
        self.disabled: bool = True
        self.hash: imagehash.ImageHash = None
        self.date: int = None
        self.inode: int = None
        self.group: List[ImageFile] = None

        img: Image.Image = None
        try:
            img = Image.open(path)
        except Exception as e:
            print(f"Error opening image {path}: {e}")
            return
        try:
            self.hash = imagehash.phash(img)
        except Exception as e:
            print(f"Error calculating hash for image {path}: {e}")
            return
        self.disabled = False
        self.date = None
        if hasattr(img, '_getexif'):
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

    def to_dict(self) -> Dict[str, Any]:
        """
        画像ファイルの情報を辞書形式で返す。
        """
        thumbnail = ""
        try:
            with Image.open(self.paths[0]) as img:
                img.thumbnail((128, 128))
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                thumbnail = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating thumbnail for {self.path[0]}: {e}")

        return {
            "paths": self.paths,
            "size": self.size,
            "date": self.date.strftime('%Y/%m/%d %H:%M:%S'),
            "thumbnail": thumbnail
        }

    def __repr__(self) -> str:
        return f"ImageFile({self.paths}, size={self.size}, hash={self.hash}, date={self.date})"

# グローバル変数で進捗状況を管理
progress_init: Dict[str, Any] = {
        "time": "",
        "progress": 0,
        "page": "/settings",
        "status": "未開始",
        "message": "",
        "steps": [
            {"name": "画像ファイルの一覧作成", "progress": '?', "status": "未開始"},
            {"name": "画像ファイルのハッシュ計算", "progress": 0, "status": "未開始"},
            {"name": "類似画像のグルーピング", "progress": 0, "status": "未開始"},
        ],
        "group_list": []
    }

progress_data: Dict[str, Any] = deepcopy(progress_init)
paths: Dict[str, ImageFile] = {}
inode_map: Dict[int, ImageFile] = {}
group_list: List[List[ImageFile]] = []

def get_progress() -> Dict[str, Any]:
    """
    現在の進捗状況を返す。
    """
    global progress_data
    progress_data["time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    return progress_data

def background_image_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    画像探索処理をバックグラウンドで実行する。
    """
    global progress_data
    global paths
    global inode_map
    global group_list

    # ステップ 1: 画像ファイルの一覧作成
    progress_data = deepcopy(progress_init)
    paths = {}
    inode_map = {}
    group_list = []
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
            if not image.disabled:
                images.append(image)
            progress_data["steps"][1]["progress"] = ((index + 1) * 10000 // len(image_files)) / 100
            progress_data["message"] = f"ハッシュ計算中: {index + 1}/{len(image_files)}"
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")
    progress_data["steps"][1]["status"] = "完了"

    # ステップ 3: 類似画像のグルーピング
    progress_data["status"] = "グルーピング中"
    progress_data["steps"][2]["status"] = "進行中"
    for index, img in enumerate(images):
        # 既にハードリンクされたファイルはスキップ
        if img.inode in inode_map:
            inode_map[img.inode].paths.extend(img.paths)
            for path in img.paths:
                paths[path] = inode_map[img.inode]
            continue
        inode_map[img.inode] = img
        for path in img.paths:
            paths[path] = img
        # 既存のグループに追加するか新規のグループを作るか判定する
        for group in group_list:
            if any(abs(img.hash - other.hash) == 0 for other in group):
                group.append(img)
                img.group = group
                break
        else:
            group_list.append([img])
            img.group = group_list[-1]
        progress_data["steps"][2]["progress"] = ((index + 1) * 10000 // len(images)) / 100
        progress_data["message"] = f"グルーピング中: {index + 1}/{len(images)}, グループ数: {len(group_list)}"
    progress_data["steps"][2]["progress"] = 100
    progress_data["steps"][2]["status"] = "完了"

    # 重複画像のあるグループのみをリストに登録する
    progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
    progress_data["message"] = f"画像探索処理が完了しました。イメージ数 {len(images)} 件、グループ数 {len(group_list)} 件、重複のあるグループは {len(progress_data['group_list'])} 件。"
    # 全体の進捗を完了に設定
    progress_data["progress"] = 100
    progress_data["page"] = "/results"
    progress_data["status"] = "完了"

def start_background_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    バックグラウンドで画像探索処理を開始する。
    """
    thread = threading.Thread(target=background_image_processing, args=(directory, algorithm, similarity))
    thread.start()

def handle_drag_drop_action(source: str, target: str, action: str) -> tuple[bool, str]:
    """
    ドラッグ＆ドロップのアクションを処理する。
    :param source: ソース画像のパス
    :param target: ターゲット画像のパス
    :param action: 実行するアクション (copy_date, hardlink_image, copy_image)
    :return: 成功したかどうかとメッセージ
    """
    global progress_data
    global group_list

    # グループリストを更新
    try:
        source_image = paths[source]
    except KeyError:
        return False, "Source image not found in any group."
    try:
        target_image = paths[target]
    except KeyError:
        return False, "Target image not found in any group."

    # ソースとターゲットが同じグループに属しているか確認
    if source_image.group == None:
        return False, "Source image is not in any group."
    if target_image.group == None:
        return False, "Target image is not in any group."
    if source_image.group != target_image.group:
        return False, "Source and target images are not in the same group."

    if action == "copy_date":
        # ソースの日時をターゲットにコピーする
        print(f"TODO: Copy date from {source} to {target}.")
        target_image.date = source_image.date
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        progress_data["message"] = f"{source} の日付を {target} に揃えました。"
        return True, "Date copied successfully."
    elif action == "hardlink_image":
        # ターゲットをソースのハードリンクで置き換える
        source_image.paths.extend(target_image.paths)
        target_image.group.remove(target_image)
        print(f"TODO: Replace {target} with hardlink to {source}.")
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        progress_data["message"] = f"{source} を {target} のハードリンクに置き換えました。"
        return True, "Target replaced with hardlink successfully."
    elif action == "copy_image":
        # ターゲットをソースのコピーで置き換える
        print(f"TODO: Replace {target} with copy to {source}.")
        target_image.size = source_image.size
        target_image.hash = source_image.hash
        target_image.date = source_image.date
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        progress_data["message"] = f"{source} を {target} のコピーで置き換えました。"
        return True, "Target replaced with copy successfully."
    return False, "Invalid action specified."
