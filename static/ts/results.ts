// サーバーから group_list データを取得して表示する関数
async function fetchAndDisplayGroups(): Promise<void> {
  try {
    // /progress/data からデータを取得
    const response = await fetch("/progress/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }

    const data = await response.json();
    const groupList: { paths: string[]; size: number; date: string, dateType: string, hardlink_ability: boolean, device: number, thumbnail: string }[][] = data.group_list;

    // グループを表示するコンテナ
    const container = document.getElementById("groups-container")!;
    container.innerHTML = ""; // 既存の内容をクリア

    groupList.forEach((group, groupIndex) => {
      const groupDiv = document.createElement("div");
      groupDiv.className = "group";
      if (group.length === 1) {
        groupDiv.style.opacity = "0.5"; // グループが1つだけの場合薄暗くする
      }
      // グループのタイトルを作成
      const groupTitle = document.createElement("div");
      groupTitle.className = "group-title";
      const groupTitleText = document.createElement("h2");
      groupTitleText.textContent = `グループ ${groupIndex + 1}`;
      groupTitle.appendChild(groupTitleText);
      groupDiv.appendChild(groupTitle);

      // グループ内の画像を表示
      const imagesRow = document.createElement("div");
      imagesRow.className = "images-row";
      group.forEach(image => {
        const imageItem = document.createElement("div");
        imageItem.className = "image-item";
        imageItem.draggable = true; // ドラッグ可能にする
        imageItem.dataset.imageId = image.paths[0]; // 画像のIDをデータ属性に保存
        imageItem.dataset.groupId = groupIndex.toString(); // グループのIDをデータ属性に保存

        imageItem.innerHTML = `
          <img
            src="data:image/jpeg;base64,${image.thumbnail}" alt="サムネイル"
            style="cursor: pointer;"
            src-thumbnail="data:image/jpeg;base64,${image.thumbnail}" 
            src-real="/api/image?path=${encodeURIComponent(image.paths[0])}"
          >
          <div class="image-info">
            <ul>${image.paths.map(path => `<li>${path}</li>`).join("")}</ul>
            <p>サイズ: ${image.size} bytes</p>
            <p>日付: ${image.date} ${image.dateType === "exif" ? "(EXIF情報/更新不可)" : ""}</p>
          </div>
        `;

        // ドラッグイベントを追加
        imageItem.addEventListener("dragstart", (event) => {
          event.dataTransfer?.setData("imageId", imageItem.dataset.imageId!);
          event.dataTransfer?.setData("groupId", imageItem.dataset.groupId!);
        });
        imageItem.addEventListener("dragover", (event) => {
          event.preventDefault(); // ドロップを許可
        });
        imageItem.addEventListener("drop", async (event) => {
          event.preventDefault();
          // 既存の選択メニューを削除する
          const existingMenu = document.querySelector(".action-menu");
          if (existingMenu) {
            document.body.removeChild(existingMenu);
          }
          // ドロップ元とドロップ先の情報を確認する
          const sourcePath = event.dataTransfer?.getData("imageId");
          const sourceGroupId = event.dataTransfer?.getData("groupId");
          const targetPath = image.paths[0];
          const targetGroupId = groupIndex.toString();
          if (sourcePath && targetPath && sourcePath !== targetPath && sourceGroupId === targetGroupId) {
            // 選択メニューを作成する
            const actionMenu = document.createElement("div");
            actionMenu.className = "action-menu";
            actionMenu.style.display = "flex";
            actionMenu.style.flexDirection = "column";
            // 各アクションのボタンを作成する
            const dateCopyButton = document.createElement("button");
            dateCopyButton.textContent = "日付のコピー";
            dateCopyButton.disabled = image.dateType === "exif"; // EXIF情報の場合は無効
            dateCopyButton.addEventListener("click", async () => {
              await executeAction("copy_date", sourcePath, targetPath);
              document.body.removeChild(actionMenu);
            });
            const hardlinkButton = document.createElement("button");
            hardlinkButton.textContent = "ハードリンクによる置き換え";
            hardlinkButton.disabled = !(image.hardlink_ability && image.device === group[0].device); // デバイスが異なる場合は無効
            hardlinkButton.addEventListener("click", async () => {
              await executeAction("hardlink_image", sourcePath, targetPath);
              document.body.removeChild(actionMenu);
            });
            const copyButton = document.createElement("button");
            copyButton.textContent = "コピーによる置き換え";
            copyButton.addEventListener("click", async () => {
              await executeAction("copy_image", sourcePath, targetPath);
              document.body.removeChild(actionMenu);
            });
            const cancelButton = document.createElement("button");
            cancelButton.textContent = "キャンセル";
            cancelButton.addEventListener("click", () => {
              document.body.removeChild(actionMenu);
            });
            // 選択メニューにボタンを追加する
            actionMenu.appendChild(dateCopyButton);
            actionMenu.appendChild(hardlinkButton);
            actionMenu.appendChild(copyButton);
            actionMenu.appendChild(cancelButton);

            // 選択メニューを表示する
            document.body.appendChild(actionMenu);
            actionMenu.style.position = "absolute";
            actionMenu.style.top = `${event.pageY}px`;
            actionMenu.style.left = `${event.pageX}px`;

            // ESC キーでもキャンセルする
            const escKeyListener = (event: KeyboardEvent) => {
              if (event.key === "Escape") {
                document.body.removeChild(actionMenu);
                document.removeEventListener("keydown", escKeyListener);
              }
            };
            document.addEventListener("keydown", escKeyListener);
          }
        });
        // クリックイベントを追加
        const imgElement = imageItem.querySelector("img")!;
        imgElement.addEventListener("click", () => toggleImage(imgElement));

        imagesRow.appendChild(imageItem);
      });

      groupDiv.appendChild(imagesRow);
      container.appendChild(groupDiv);
    });
  } catch (error) {
    console.error("グループデータの取得中にエラーが発生しました:", error);
  }
}

// 選択したアクションを実行する
async function executeAction(action: string, sourcePath: string, targetPath: string): Promise<void> {
  const response = await fetch("/api/handle_drag_drop", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action: action,
      source: sourcePath,
      target: targetPath,
    }),
  });

  if (response.ok) {
    // 成功したら結果を取得しなおす
    fetchAndDisplayGroups();
  } else {
    console.error("アクションの実行中にエラーが発生しました:", response.statusText);
  }
}

// サムネイルとリアル画像を切り替える関数
function toggleImage(imgElement: HTMLImageElement): void {
  const currentSrc = imgElement.src;
  const thumbnailSrc = imgElement.getAttribute("src-thumbnail")!;
  const realSrc = imgElement.getAttribute("src-real")!;

  // 現在の画像がサムネイルならリアル画像に切り替え、そうでなければサムネイルに戻す
  if (currentSrc === thumbnailSrc) {
    imgElement.src = realSrc;
    imgElement.alt = "実際の画像";
    imgElement.style.height = "100vh"
  } else {
    imgElement.src = thumbnailSrc;
    imgElement.alt = "サムネイル";
    imgElement.style.height = "128px"
  }
}

// ページ読み込み時にデータを取得して表示
document.addEventListener("DOMContentLoaded", fetchAndDisplayGroups);
