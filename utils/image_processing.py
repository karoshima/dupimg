import base64
import imagehash
import os
import threading
import traceback
import shutil
from utils.profile import profile
from datetime import datetime
from copy import deepcopy
from io import BytesIO
from typing import List, Any, Dict
from PIL import Image

hardlink_ability_table: Dict[int, bool] = {}

def hardlink_ability(path: str, dev: int) -> bool:
    """
    ハードリンクの作成が可能かどうかを確認する。
    :param path: ファイルパス
    :param dev: デバイス番号
    :return: ハードリンクの作成が可能ならTrue、そうでなければFalse
    """
    if dev in hardlink_ability_table:
        return hardlink_ability_table[dev]
    # キャッシュがなければ実地調査する
    if not os.path.exists(path):
        # 判定不能
        return False
    # ハードリンクの作成を試みた結果を返す
    # 返り値は hardlink_ability_table にキャッシュする
    testpath = path + ".test"
    try:
        os.link(path, testpath)
        os.remove(testpath)
        hardlink_ability_table[dev] = True
        return True
    except OSError:
        hardlink_ability_table[dev] = False
    except Exception as e:
        print(f"Cache create for device {dev}: {hardlink_ability_table}")
        hardlink_ability_table[dev] = False
        # 例外が発生した場合はハードリンクの作成ができないとみなす
        # ただし、例外の内容によっては True を返すこともあるかもしれないので注意
        # ここでは False を返す
    return False

class ImageFile:
    """
    画像ファイルに関する様々なを表すクラス。
    """
    def __init__(self, path: str) -> None:
        self.paths: List[str] = [path]
        self.size: int = os.path.getsize(path)
        self.disabled: bool = True
        self.hash: imagehash.ImageHash = None
        self.exifdate: datetime.datetime = None
        self.filedate: datetime.datetime = None
        self.inode: int = None
        self.hardlink_ability: bool = False
        self.device: int = None
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
        self.exifdate = None
        exif_data = img.getexif()
        date_str = exif_data.get(36867) or exif_data.get(306)
        if date_str:
            for fmt in [ "%Y:%m:%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                try:
                    self.exifdate = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                print(f"Unsupported date format in {path}: {date_str}")
        self.filedate = datetime.fromtimestamp(os.path.getmtime(path))
        self.device = os.stat(path).st_dev
        self.inode = os.stat(path).st_ino
        self.hardlink_ability = hardlink_ability(path, self.device)

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
            print(f"Error generating thumbnail for {self.paths[0]}: {e}")

        return {
            "paths": self.paths,
            "size": self.size,
            "date": (self.exifdate or self.filedate).strftime('%Y/%m/%d %H:%M:%S'),
            "dateType": "exif" if self.exifdate else "file",
            "hardlink_ability": self.hardlink_ability,
            "device": self.device,
            "thumbnail": thumbnail
        }

    def __repr__(self) -> str:
        return f"ImageFile({self.paths}, size={self.size}, hash={self.hash}, date={self.exifdate or self.filedate}({'exif' if self.exifdate else 'file'}), inode={self.inode})"

# グローバル変数で進捗状況を管理
progress_init: Dict[str, Any] = {
        "current_time": "",
        "elapsed_time": "",
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
start_time: datetime = None
finish_time: datetime = None
paths: Dict[str, ImageFile] = {}
inode_map: Dict[int, ImageFile] = {}
group_list: List[List[ImageFile]] = []

def get_progress() -> Dict[str, Any]:
    """
    現在の進捗状況を返す。
    """
    global progress_data
    global start_time
    global finish_time

    elapsed_time = ((finish_time or datetime.now()) - start_time).total_seconds() if start_time else 0
    days, rem = divmod(elapsed_time, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    daystr = f"{int(days)}日 " if days > 0 else ""
    hourstr = f"{int(hours)}時間 " if hours > 0 or days > 0 else ""
    minutestr = f"{int(minutes)}分 " if minutes > 0 or hours > 0 or days > 0 else ""
    secondstr = f"{seconds}秒"
    progress_data["current_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    progress_data["elapsed_time"] = daystr + hourstr + minutestr + secondstr
    print(f"start_time: {start_time}, finish_time: {finish_time}, elapsed_time: {progress_data['elapsed_time']}")
    return progress_data

@profile
def background_image_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    画像探索処理をバックグラウンドで実行する。
    """
    global progress_data
    global start_time
    global finish_time
    global paths
    global inode_map
    global group_list

    # ステップ 1: 画像ファイルの一覧作成
    progress_data = deepcopy(progress_init)
    start_time = datetime.now()
    finish_time = None
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
            traceback.print_exc()
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
    finish_time = datetime.now()

def start_background_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    """
    バックグラウンドで画像探索処理を開始する。
    """
    thread = threading.Thread(target=background_image_processing, args=(directory, algorithm, similarity))
    thread.start()

def replace_with_hardlink(source: ImageFile, target: ImageFile) -> tuple[bool, str]:
    """
    ソース画像をターゲット画像のハードリンクで置き換える。
    :param source: ソース画像
    :param target: ターゲット画像
    :return: 成功したかどうかとメッセージ
    """
    # source がちゃんとあることを確認する
    if not os.path.exists(source.paths[0]):
        return False, f"Source image {source.paths[0]} does not exist."
    # source から target にハードリンクできることを確認する
    if not target.hardlink_ability:
        return False, f"Target image {target.paths[0]} cannot be hardlinked."
    if source.device != target.device:
        return False, f"Source and target images are on different devices: {source.device} and {target.device}."

    msg: str = "" # エラーメッセージ
    replacedpath: List[str] = [] # 上書き成功したファイル
    failedpath: List[str] = [] # 上書き失敗したファイル

    # ターゲットの各パスに対して、ハードリンクによる置き換えを行なう
    for path in target.paths: 
        print(f"Replacing {path} with hardlink to {source.paths[0]}")
        if not os.path.exists(path):
            print(f"Target image {path} does not exist.")
            msg += f"Target image {path} does not exist."
            continue
        # 置き換え失敗に備えてバックアップを作成する
        save_path = path + ".bak"
        while os.path.exists(save_path):
            save_path = save_path + "_"
        try:
            os.rename(path, save_path)
        except OSError as e:
            print(f"Error creating backup {path} to {save_path}: {e}")
            msg += f"Error creating backup {path} to {save_path}: {e}"
            failedpath.append(path)
            continue
        # ハードリンクで置き換える
        try:
            os.link(source.paths[0], path)
        except OSError as e:
            print(f"Error creating hardlink from {source.paths[0]} to {path}: {e}")
            msg += f"Error creating hardlink from {source.paths[0]} to {path}: {e}"
            failedpath.append(path)
            # 失敗につき、バックアップを戻す
            try:
                os.rename(save_path, path)
            except OSError as e:
                print(f"Error restoring backup {save_path} to {path}: {e}")
                msg += f"Error restoring backup {save_path} to {path}: {e}"
            continue
        # ハードリンクの作成に成功したので、バックアップを削除する
        try:
            os.remove(save_path)
        except OSError as e:
            print(f"Error removing backup {save_path}: {e}")
            msg += f"Error removing backup {save_path}: {e}"
        replacedpath.append(path)
        source.paths.append(path)
        print(f"Replaced {path} with hardlink to {source.paths[0]}")
    target.paths = failedpath
    print(f"Target paths after replacement: {target.paths}")
    return True, f"Replaced {replacedpath} with hardlink to {source.paths[0]}."

def replace_with_copy(source: ImageFile, target: ImageFile) -> tuple[bool, str]:
    """
    ソース画像をターゲット画像のコピーで置き換える。
    :param source: ソース画像
    :param target: ターゲット画像
    :return: 成功したかどうかとメッセージ
    """
    # ターゲットのパス[0]に対して、コピーによる置き換えを行なう
    try:
        shutil.copy2(source.paths[0], target.paths[0])
    except FileNotFoundError as e:
        return False, f"Source image {source.paths[0]} does not exist."
    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except shutil.SameFileError as e:
        return False, f"Source and target are the same file: {e}"
    except Exception as e:
        return False, f"Error copying {source.paths[0]} to {target.paths[0]}: {e}"
    copied = ImageFile(target.paths.pop(0))
    target.group.append(copied)
    return replace_with_hardlink(copied, target)

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
        if target_image.exifdate:
            return False, "Target image already has EXIF date."
        new_date = (source_image.exifdate or source_image.filedate).timestamp()
        os.utime(target_image.paths[0], (new_date, new_date))
        target_image.filedate = source_image.exifdate or source_image.filedate
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        progress_data["message"] = f"{source} の日付を {target} に揃えました。"
        return True, "Date copied successfully."
    elif action == "hardlink_image":
        # ターゲットをソースのハードリンクで置き換える
        result, msg = replace_with_hardlink(source_image, target_image)
        if len(target_image.paths) == 0:
            # ソースのパスが空になった場合、ソースをグループから削除
            target_image.group.remove(target_image)
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        if result:
            progress_data["message"] = f"{source} を {target} のハードリンクに置き換えました。"
        else:
            progress_data["message"] = f"{source} を {target} のハードリンクに置き換えられませんでした。{msg}"
        return result, msg
    elif action == "copy_image":
        # ターゲットをソースのコピーで置き換える
        print(f"TODO: Replace {target} with copy to {source}.")
        target_image.size = source_image.size
        target_image.hash = source_image.hash
        target_image.exifdate = source_image.exifdate
        target_image.filedate = source_image.filedate
        progress_data["group_list"] = list(map(lambda x: list(map(lambda y: y.to_dict(), x)), filter(lambda x: len(x) > 1 or len(x[0].paths) > 1, group_list)))
        progress_data["message"] = f"{source} を {target} のコピーで置き換えました。"
        return True, "Target replaced with copy successfully."
    return False, "Invalid action specified."
