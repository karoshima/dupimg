// サーバーから group_list データを取得して表示する関数
async function fetchAndDisplayGroups(): Promise<void> {
  try {
    // /progress/data からデータを取得
    const response = await fetch("/progress/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }

    const data = await response.json();
    const groupList: { paths: string[]; size: number; date: string, dateType: string, thumbnail: string }[][] = data.group_list;

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
            const dateCopyOption = image.dateType === "exif"
              ? `<option value="copy_date" disabled>日付のコピー (EXIF情報のため無効)</option>`
              : `<option value="copy_date">日付のコピー</option>`;
            actionMenu.innerHTML = `
              <label for="action-select">アクションを選択してください:</label>
              <select id="action-select">
                ${dateCopyOption}
                <option value="hardlink_image">ハードリンクによる置き換え</option>
                <option value="copy_image">コピーによる置き換え</option>
              </select>
              <button id="action-confirm">実行</button>
              <button id="action-cancel">キャンセル</button>
            `;
            document.body.appendChild(actionMenu);
            // 選択メニューの位置を調整する
            actionMenu.style.position = "absolute";
            actionMenu.style.top = `${event.clientY}px`;
            actionMenu.style.left = `${event.clientX}px`;
            // 実行ボタンのクリックイベント
            const confirmButton = actionMenu.querySelector("#action-confirm")!;
            confirmButton.addEventListener("click", async () => {
              const action = (actionMenu.querySelector("#action-select") as HTMLSelectElement).value;
              // バックエンドにリクエストを送信する
              const response = await fetch("/api/handle_drag_drop", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  source: sourcePath,
                  target: targetPath,
                  action: action,
                })
              });
              if (response.ok) {
                // 成功したら結果を取得しなおす
                fetchAndDisplayGroups();
              } else {
                console.log("ドラッグ＆ドロップの処理に失敗しました:", response.statusText);
              }
              // アクションメニューを削除
              document.body.removeChild(actionMenu);
            });
            // キャンセルボタンのクリックイベント
            const cancelButton = actionMenu.querySelector("#action-cancel")!;
            cancelButton.addEventListener("click", () => {
              // アクションメニューを削除
              document.body.removeChild(actionMenu);
            });
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
