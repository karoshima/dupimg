// サーバーから group_list データを取得して表示する関数
async function fetchAndDisplayGroups(): Promise<void> {
  try {
    // /progress/data からデータを取得
    const response = await fetch("/progress/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }

    const data = await response.json();
    const groupList: { path: string; size: number; date: string, thumbnail: string }[][] = data.group_list;

    // グループを表示するコンテナ
    const container = document.getElementById("groups-container")!;
    container.innerHTML = ""; // 既存の内容をクリア

    groupList.forEach((group, groupIndex) => {
      const groupDiv = document.createElement("div");
      groupDiv.className = "group";
      groupDiv.innerHTML = `<h2>グループ ${groupIndex + 1}</h2>`;

      group.forEach(image => {
        const imageItem = document.createElement("div");
        imageItem.className = "image-item";

        imageItem.innerHTML = `
          <img
            src="data:image/jpeg;base64,${image.thumbnail}" alt="サムネイル"
            style="cursor: pointer;"
            src-thumbnail="data:image/jpeg;base64,${image.thumbnail}" 
            src-real="/api/image?path=${encodeURIComponent(image.path)}"
          >
          <div class="image-info">
            <p>パス: ${image.path}</p>
            <p>サイズ: ${image.size} bytes</p>
            <p>日付: ${image.date}</p>
          </div>
        `;

        // クリックイベントを追加
        const imgElement = imageItem.querySelector("img")!;
        imgElement.addEventListener("click", () => toggleImage(imgElement));

        groupDiv.appendChild(imageItem);
      });

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
