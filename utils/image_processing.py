import base64
import imagehash
import os
import threading
import traceback
import shutil
import sqlite3
import json
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
            for fmt in ["%Y:%m:%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
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

    def to_sqlite_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "inode": self.inode,
            "paths": json.dumps(self.paths),
            "size": self.size,
            "hash": str(self.hash) if self.hash else None,
            "exifdate": self.exifdate.strftime('%Y-%m-%d %H:%M:%S') if self.exifdate else None,
            "filedate": self.filedate.strftime('%Y-%m-%d %H:%M:%S') if self.filedate else None,
            "hardlink_ability": int(self.hardlink_ability),
        }

    @classmethod
    def from_sqlite_row(cls, row: Dict[str, Any]) -> "ImageFile":
        obj = cls.__new__(cls)
        obj.device = row["device"]
        obj.inode = row["inode"]
        obj.paths = json.loads(row["paths"])
        obj.size = row["size"]
        obj.hash = imagehash.hex_to_hash(row["hash"]) if row["hash"] else None
        obj.exifdate = datetime.strptime(row["exifdate"], '%Y-%m-%d %H:%M:%S') if row["exifdate"] else None
        obj.filedate = datetime.strptime(row["filedate"], '%Y-%m-%d %H:%M:%S') if row["filedate"] else None
        obj.hardlink_ability = bool(row["hardlink_ability"])
        obj.disabled = False
        return obj

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
        {"name": "画像ファイルの一覧作成", "progress": 0, "status": "未開始"},
        {"name": "画像ファイルのハッシュ計算", "progress": 0, "status": "未開始"},
        {"name": "類似画像のグルーピング", "progress": 0, "status": "未開始"},
    ],
    "group_list": []
}

progress_data: Dict[str, Any] = deepcopy(progress_init)
start_time: datetime = None
finish_time: datetime = None

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
    secondstr = f"{seconds:.6f}秒"
    progress_data["current_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    progress_data["elapsed_time"] = daystr + hourstr + minutestr + secondstr
    print(f"start_time: {start_time}, finish_time: {finish_time}, elapsed_time: {progress_data['elapsed_time']}")
    return progress_data

@profile
def background_image_processing(directory: List[str], algorithm: str, similarity: str) -> None:
    global progress_data, start_time, finish_time

    conn = sqlite3.connect("imagefiles.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS paths (
            path TEXT PRIMARY KEY,
            device INTEGER,
            inode INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            device INTEGER,
            inode INTEGER,
            paths TEXT,
            size INTEGER,
            hash TEXT,
            exifdate TEXT,
            filedate TEXT,
            hardlink_ability INTEGER,
            PRIMARY KEY (device, inode)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            members TEXT -- JSON: [ [device, inode], ... ]
        )
    ''')
    c.execute('DELETE FROM paths')
    c.execute('DELETE FROM images')
    c.execute('DELETE FROM groups')
    conn.commit()

    # ステップ1: 画像ファイルの一覧作成
    progress_data = deepcopy(progress_init)
    start_time = datetime.now()
    finish_time = None
    progress_data["page"] = "/progress"
    progress_data["steps"][0]["progress"] = 0
    progress_data["status"] = "一覧作成中"
    progress_data["message"] = "画像ファイルの一覧を作成しています..."
    progress_data["steps"][0]["status"] = "進行中"
    file_count = 0
    for dir in directory:
        for root, _, files in os.walk(dir):
            if ".@__thumb" in root:
                continue
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    path = os.path.join(root, file)
                    try:
                        stat = os.stat(path)
                        c.execute('INSERT OR IGNORE INTO paths VALUES (?, ?, ?)', (path, stat.st_dev, stat.st_ino))
                        file_count += 1
                        progress_data["message"] = f"画像ファイルを {file_count} 件見つけました..."
                    except Exception as e:
                        print(f"Error stat file {path}: {e}")
    conn.commit()
    progress_data["steps"][0]["progress"] = 100
    progress_data["steps"][0]["status"] = "完了"

    # ステップ2: 画像ファイルのハッシュ計算と images テーブル登録
    progress_data["status"] = "ハッシュ計算中"
    progress_data["steps"][1]["status"] = "進行中"
    c.execute('SELECT path, device, inode FROM paths')
    for index, (path, device, inode) in enumerate(c):
        try:
            image = ImageFile(path)
            if image.disabled:
                continue
            # 既存の (device, inode) があれば paths を追加
            c2 = conn.cursor()
            c2.execute('SELECT * FROM images WHERE device = ? AND inode = ?', (image.device, image.inode))
            row = c2.fetchone()
            if row:
                row_dict = dict(zip([d[0] for d in c2.description], row))
                existing = ImageFile.from_sqlite_row(row_dict)
                if path not in existing.paths:
                    existing.paths.append(path)
                    c2.execute(
                        'UPDATE images SET paths = ? WHERE device = ? AND inode = ?',
                        (json.dumps(existing.paths), image.device, image.inode)
                    )
            else:
                c2.execute(
                    'INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    tuple(image.to_sqlite_dict().values())
                )
            c2.close()
            progress_data["steps"][1]["progress"] = ((index + 1) * 10000 // file_count) / 100
            progress_data["message"] = f"ハッシュ計算中: {index + 1}/{file_count}"
        except Exception as e:
            traceback.print_exc()
            print(f"Error processing image {path}: {e}")
    conn.commit()
    progress_data["steps"][1]["status"] = "完了"

    # ステップ3: 類似画像のグルーピング
    progress_data["status"] = "グルーピング中"
    progress_data["steps"][2]["status"] = "進行中"
    c.execute('SELECT * FROM images')
    rows = c.fetchall()
    images = [ImageFile.from_sqlite_row(dict(zip([d[0] for d in c.description], row))) for row in rows]
    used = set()
    group_list = []
    for index, img in enumerate(images):
        key = (img.device, img.inode)
        if key in used:
            continue
        group = [key]
        used.add(key)
        for other in images:
            other_key = (other.device, other.inode)
            if other_key in used:
                continue
            if abs(img.hash - other.hash) == 0:
                group.append(other_key)
                used.add(other_key)
        if len(group) > 1:
            group_list.append(group)
        progress_data["steps"][2]["progress"] = ((index + 1) * 10000 // len(images)) / 100
        progress_data["message"] = f"グルーピング中: {index + 1}/{len(images)}, グループ数: {len(group_list)}"
    # groupsテーブルに保存
    for group in group_list:
        c.execute('INSERT INTO groups (members) VALUES (?)', (json.dumps(group),))
    conn.commit()
    progress_data["steps"][2]["progress"] = 100
    progress_data["steps"][2]["status"] = "完了"

    # 重複画像のあるグループのみをリストに登録する
    group_dicts = []
    for group in group_list:
        members = []
        for device, inode in group:
            c.execute('SELECT * FROM images WHERE device = ? AND inode = ?', (device, inode))
            row = c.fetchone()
            if row:
                members.append(ImageFile.from_sqlite_row(dict(zip([d[0] for d in c.description], row))).to_dict())
        group_dicts.append(members)
    progress_data["group_list"] = group_dicts
    progress_data["message"] = f"画像探索処理が完了しました。イメージ数 {len(images)} 件、グループ数 {len(group_list)} 件、重複のあるグループは {len(progress_data['group_list'])} 件。"
    # 全体の進捗を完了に設定
    progress_data["progress"] = 100
    progress_data["page"] = "/results"
    progress_data["status"] = "完了"
    finish_time = datetime.now()
    conn.close()

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
    return replace_with_hardlink(copied, target)

def handle_drag_drop_action(source_path: str, target_path: str, action: str) -> tuple[bool, str]:
    """
    ドラッグ＆ドロップのアクションを処理する。
    :param source_path: ソース画像のパス
    :param target_path: ターゲット画像のパス
    :param action: 実行するアクション (copy_date, hardlink_image, copy_image)
    :return: 成功したかどうか, メッセージ
    """
    conn = sqlite3.connect("imagefiles.db")
    c = conn.cursor()
    # pathsテーブルからdevice, inodeを取得
    c.execute('SELECT device, inode FROM paths WHERE path = ?', (source_path,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Source image not found in DB."
    source_device, source_inode = row
    c.execute('SELECT device, inode FROM paths WHERE path = ?', (target_path,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Target image not found in DB."
    target_device, target_inode = row
    # imagesテーブルからImageFileを復元
    c.execute('SELECT * FROM images WHERE device = ? AND inode = ?', (source_device, source_inode))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Source image data not found in DB."
    source_image = ImageFile.from_sqlite_row(dict(zip([d[0] for d in c.description], row)))
    c.execute('SELECT * FROM images WHERE device = ? AND inode = ?', (target_device, target_inode))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Target image data not found in DB."
    target_image = ImageFile.from_sqlite_row(dict(zip([d[0] for d in c.description], row)))
    # groupsテーブルから同じグループか確認
    c.execute('SELECT group_id, members FROM groups')
    same_group = False
    for group_id, members_json in c.fetchall():
        members = json.loads(members_json)
        if [source_device, source_inode] in members and [target_device, target_inode] in members:
            same_group = True
            break
    if not same_group:
        conn.close()
        return False, "Source and target images are not in the same group."
    if action == "copy_date":
        # ソースの日時をターゲットにコピーする
        if target_image.exifdate:
            conn.close()
            return False, "Target image already has EXIF date."
        new_date = (source_image.exifdate or source_image.filedate).timestamp()
        os.utime(target_image.paths[0], (new_date, new_date))
        target_image.filedate = source_image.exifdate or source_image.filedate
        conn.close()
        return True, "Date copied successfully."
    elif action == "hardlink_image":
        # ターゲットをソースのハードリンクで置き換える
        result, msg = replace_with_hardlink(source_image, target_image)
        conn.close()
        return result, msg
    elif action == "copy_image":
        result, msg = replace_with_copy(source_image, target_image)
        conn.close()
        return result, msg
    conn.close()
    return False, "Invalid action specified."

def image_path_exists(path: str) -> bool:
    conn = sqlite3.connect("imagefiles.db")
    c = conn.cursor()
    c.execute('SELECT 1 FROM paths WHERE path = ?', (path,))
    exists = c.fetchone() is not None
    conn.close()
    return exists
