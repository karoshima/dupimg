// フォームの送信イベントをリッスン
export function initialize(): void {
  const settingsForm = document.getElementById("settings-form") as HTMLFormElement;

  settingsForm.addEventListener("submit", async (event: Event) => {
    event.preventDefault(); // フォームのデフォルト動作を無効化

    const formData = new FormData(settingsForm);
    formData.append("directories", JSON.stringify(selectedDirectories)); // ディレクトリリストを追加

    try {
      const response = await fetch("/settings", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTPエラー: ${response.status}`);
      }

      const result = await response.json();
      console.log(result); // サーバーからのレスポンスを確認
      alert(`選択されたディレクトリ: ${result.directories}`);
    } catch (error) {
      console.error("エラーが発生しました:", error);
      alert("エラーが発生しました。詳細はコンソールを確認してください。");
    }
  });
}
// DOMContentLoaded イベントで初期化
document.addEventListener("DOMContentLoaded", initialize);

// 選択されたディレクトリを管理するリスト
const selectedDirectories: string[] = [];

// ディレクトリをリストに追加する関数
function addDirectory(directory: string): void {
  if (!directory.startsWith("/")) {
    alert("絶対パスを入力してください。相対パスは使用できません。");
    return;
  }
  if (!directory || selectedDirectories.includes(directory)) {
    alert("ディレクトリが空、または既に追加されています。");
    return;
  }

  selectedDirectories.push(directory);

  const directoryList = document.getElementById("selected-directories") as HTMLUListElement;
  const listItem = document.createElement("li");
  listItem.textContent = directory;

  // ディレクトリ選択機能を追加
  listItem.addEventListener("click", () => {
    const directoryInput = document.getElementById("directory") as HTMLInputElement;
    directoryInput.value = directory; // 選択されたディレクトリをテキストボックスに表示
    alert(`ディレクトリ "${directory}" が選択されました`);
  });

  // 削除ボタンを追加
  const removeButton = document.createElement("button");
  removeButton.textContent = "削除";
  removeButton.style.marginLeft = "10px";
  removeButton.addEventListener("click", () => {
    const index = selectedDirectories.indexOf(directory);
    if (index > -1) {
      selectedDirectories.splice(index, 1);
    }
    listItem.remove();

    // 最初のディレクトリが削除された場合、次のディレクトリを選択
    const directoryInput = document.getElementById("directory") as HTMLInputElement;
    if (selectedDirectories.length > 0) {
      directoryInput.value = selectedDirectories[0];
    } else {
      directoryInput.value = ""; // リストが空の場合はクリア
    }
  });

  listItem.appendChild(removeButton);
  directoryList.appendChild(listItem);
}

// 「追加」ボタンのクリックイベント
document.getElementById("add-directory")?.addEventListener("click", () => {
  const directoryInput = document.getElementById("directory") as HTMLInputElement;
  const directory = directoryInput.value.trim();
  addDirectory(directory);
  directoryInput.value = ""; // 入力欄をクリア
});

// エクスプローラー的なディレクトリ選択機能
document.getElementById("select-directory")?.addEventListener("click", async () => {
  const directoryList = document.getElementById("directory-list") as HTMLUListElement;
  directoryList.innerHTML = ""; // リストをクリア

  // 初期ディレクトリを取得
  await fetchDirectories("/", directoryList);

  // ポップアップを表示
  showPopup();
});

// ポップアップを閉じる
document.getElementById("close-popup")?.addEventListener("click", () => {
  hidePopup();
});

// ポップアップを表示する関数
export function showPopup(): void {
  const popup = document.getElementById("directory-popup") as HTMLDivElement;
  if (popup) {
    popup.style.display = "block";
  }
}

// ポップアップを非表示にする関数
export function hidePopup(): void {
  const popup = document.getElementById("directory-popup") as HTMLDivElement;
  if (popup) {
    popup.style.display = "none";
  }
}

// ディレクトリ構造を取得して表示する関数
export async function fetchDirectories(path: string, parentElement: HTMLUListElement): Promise<void> {
  try {
    const response = await fetch(`/list_directories?path=${encodeURIComponent(path)}`);
    const data = await response.json();

    if (data.status === "success") {
      data.directories.forEach((dir: { name: string; path: string }) => {
        const listItem = document.createElement("li");
        listItem.textContent = dir.name;
        listItem.dataset.path = dir.path;

        // ディレクトリ選択とサブディレクトリの開閉を1つのクリックイベントで実現
        listItem.addEventListener("click", async (event) => {
          event.stopPropagation(); // イベントの伝播を防止

          // ディレクトリを選択
          const directoryInput = document.getElementById("directory") as HTMLInputElement;
          directoryInput.value = dir.path; // 選択されたディレクトリをテキストボックスに表示
          // alert(`ディレクトリ "${dir.path}" が選択されました`);

          // サブディレクトリの開閉
          if (listItem.classList.contains("expanded")) {
            // 折りたたむ
            const subList = listItem.querySelector("ul");
            if (subList) {
              subList.remove();
            }
            listItem.classList.remove("expanded");
          } else {
            // 展開する
            const subList = document.createElement("ul");
            listItem.appendChild(subList);
            await fetchDirectories(dir.path, subList);
            listItem.classList.add("expanded");
          }
        });

        parentElement.appendChild(listItem);
      });
    } else {
      alert(`エラー: ${data.message}`);
    }
  } catch (error) {
    console.error("ディレクトリの取得中にエラーが発生しました:", error);
  }
}
