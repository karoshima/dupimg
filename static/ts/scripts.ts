// 選択されたディレクトリを管理するリスト
const selectedDirectories: Set<string> = new Set();

// ページ遷移中かどうかを示すフラグ
// - 「検出開始」ボタンが押された際に true に設定され、ページ遷移が完了するまで維持される。
// - fetchDirectories() 内でエラーが発生した場合、このフラグを参照してページ遷移中のエラーを無視する。
let isPageNavigating = false;

// パスが別のパスのサブディレクトリかどうかを判定する関数
// @param parent - 親ディレクトリのパス
// @param child - 子ディレクトリのパス
// @returns - サブディレクトリの場合は true、そうでない場合は false
function isSubdirectory(parent: string, child: string): boolean {
  const normalizedParent = parent.endsWith("/") ? parent : parent + "/";
  const normalizedChild = child.endsWith("/") ? child : child + "/";
  return normalizedChild.startsWith(normalizedParent) && normalizedParent !== normalizedChild;
}

// 指定されたディレクトリが他のディレクトリのサブディレクトリかどうかを判定する関数
// @param dir - 判定対象のディレクトリ
// @param directories - 判定に使用するディレクトリのリスト
// @returns サブディレクトリであれば true、それ以外は false
function isSubdirectoryOfAny(dir: string, directories: string[]): boolean {
  return directories.some((parent) => isSubdirectory(parent, dir));
}

// フォームの送信イベントをリッスン
// DOMContentLoaded イベントで初期化
document.addEventListener("DOMContentLoaded", () => {
  const settingsForm = document.getElementById("settings-form") as HTMLFormElement;
  console.log("isPageNavigating: false -> true");
  isPageNavigating = true; // ページ遷移時の /list_directories エラーを無視するために true に設定する
  updateStartButtonState(); // 初期状態でボタンを更新

  settingsForm.addEventListener("submit", async (event: Event) => {
    event.preventDefault(); // フォームのデフォルト動作を無効化

    // 他ディレクトリのサブディレクトリになっているものを除外する
    const directories = Array.from(selectedDirectories);
    const filteredDirectories = directories.filter((dir) => !isSubdirectoryOfAny(dir, directories));
    console.log("フィルタリングされたディレクトリ:", filteredDirectories);

    const formData = new FormData(settingsForm);
    formData.append("directories", JSON.stringify(filteredDirectories)); // ディレクトリリストを追加

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
      window.location.href = "/progress"; // フォーム送信後にリダイレクト
    } catch (error) {
      console.error("エラーが発生しました:", error);
      alert("エラーが発生しました。詳細はコンソールを確認してください。");
      console.log("isPageNavigating: true -> false");
      isPageNavigating = false; // ページ遷移が完了したのでフラグをリセット
    }
  });
});

// 「検出開始」ボタンの有効化/無効化を制御する関数
function updateStartButtonState(): void {
  const startButton = document.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (startButton) {
    startButton.disabled = selectedDirectories.size === 0; // ディレクトリが空なら無効化
  }
}

// ディレクトリをリストに追加する関数
// @param directory - 追加するディレクトリのパス
function addDirectory(directory: string): void {
  if (!directory.startsWith("/")) {
    alert("絶対パスを入力してください。相対パスは使用できません。");
    return;
  }
  // ディレクトリを正規化
  const normalizedDirectory = directory.endsWith("/") ? directory.slice(0, -1) : directory;
  if (selectedDirectories.has(normalizedDirectory)) {
    alert("このディレクトリは既に選択されています。");
    return;
  }

  selectedDirectories.add(directory);

  showDirectory()
  updateStartButtonState(); // ボタンの状態を更新
}

// 選択されたディレクトリを表示する関数
function showDirectory(): void {
  const directoryList = document.getElementById("selected-directories") as HTMLUListElement;
  directoryList.innerHTML = ""; // リストをクリア

  const directories = Array.from(selectedDirectories).sort(); // ソートして階層構造を安定化
  const parentMap: Map<string, HTMLLIElement> = new Map();

  directories.forEach((dir) => {
    const listItem = document.createElement("li");
    listItem.textContent = dir;
    listItem.dataset.path = dir;

    // 削除ボタンを追加
    const removeButton = document.createElement("button");
    removeButton.textContent = "削除";
    removeButton.style.marginLeft = "10px";
    removeButton.addEventListener("click", () => {
      selectedDirectories.delete(dir);
      listItem.remove();
      showDirectory();
      updateStartButtonState(); // ボタンの状態を更新
    });

    listItem.appendChild(removeButton);

    // サブディレクトリかどうかを判定
    let isChild = false;
    parentMap.forEach((parentItem, parentPath) => {
      if (isSubdirectory(parentPath, dir)) {
        // サブディレクトリの場合、親の下に追加
        const subList = parentItem.querySelector("ul") || document.createElement("ul");
        subList.style.opacity = "0.5"; // 文字を薄く表示
        parentItem.appendChild(subList);
        subList.appendChild(listItem);
        isChild = true;
      }
    });
    // サブディレクトリでない場合、トップレベルに追加
    if (!isChild) {
      directoryList.appendChild(listItem);
      parentMap.set(dir, listItem);
    }
  });
}

// 「追加」ボタンのクリックイベント
document.getElementById("add-directory")?.addEventListener("click", async () => {
  const directoryInput = document.getElementById("directory") as HTMLInputElement;
  const directory = directoryInput.value.trim();
  try {
    const response = await fetch("/add_directory", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ directory }),
    });

    const data = await response.json();
    if (data.status === "success") {
      addDirectory(directory);
    } else {
      alert(`エラー: ${data.message}`);
    }
  } catch (error) {
    console.error("ディレクトリの追加中にエラーが発生しました:", error);
  }
  directoryInput.value = ""; // 入力欄をクリア
});

// エクスプローラー的なディレクトリ選択機能
document.getElementById("select-directory")?.addEventListener("click", async () => {
  const directoryList = document.getElementById("directory-list") as HTMLUListElement;
  directoryList.innerHTML = ""; // リストをクリア

  // 初期ディレクトリを取得
  await fetchDirectories("", directoryList);

  // ポップアップを表示
  showPopup();
});

// ポップアップを閉じる
document.getElementById("close-popup")?.addEventListener("click", () => {
  hidePopup();
});

// ポップアップを表示する関数
function showPopup(): void {
  const popup = document.getElementById("directory-popup") as HTMLDivElement;
  if (popup) {
    popup.style.display = "block";
  }
}

// ポップアップを非表示にする関数
function hidePopup(): void {
  const popup = document.getElementById("directory-popup") as HTMLDivElement;
  if (popup) {
    popup.style.display = "none";
  }
}

// ディレクトリ構造を取得して表示する関数
async function fetchDirectories(path: string, parentElement: HTMLUListElement): Promise<void> {
  try {
    console.log("fetchDirectories() called with path:", path);
    const response = await fetch(`/list_directories?path=${encodeURIComponent(path)}`);
    console.log("/list_directories response:", response);
    const data = await response.json();

    if (data.status === "success") {
      data.directories
      .sort((a: { name: string }, b: { name: string }) => a.name.localeCompare(b.name)) // 名前でソート
      .forEach((dir: { name: string; path: string }) => {
        const listItem = document.createElement("li");
        listItem.dataset.path = dir.path;

        // 「追加」ボタン
        const addButton = document.createElement("button");
        addButton.textContent = "追加";
        addButton.style.marginLeft = "10px";
        addButton.addEventListener("click", () => {
          addDirectory(dir.path);
        });

        // 「開く」ボタン
        const openButton = document.createElement("button");
        openButton.textContent = "開く";
        openButton.style.marginLeft = "10px";
        openButton.style.display = "inline-block"; // 初期状態では有効
        openButton.disabled = false; // 初期状態では有効

        // 「閉じる」ボタン
        const closeButton = document.createElement("button");
        closeButton.textContent = "閉じる";
        closeButton.style.marginLeft = "10px";
        closeButton.style.display = "none"; // 初期状態では無効化

        // 「開く」の動作
        openButton.addEventListener("click", async () => {
          if (openButton.style.display == "none") return; // クリック不可の場合は何もしない
          openButton.disabled = true;
          openButton.textContent = "(展開中)";
          closeButton.style.display = "inline-block"; // 「閉じる」ボタンを有効化

          const subList = document.createElement("ul");
          listItem.appendChild(subList);

          try {
            await fetchDirectories(dir.path, subList);
            // await 中に「閉じる」されてなければ、「開く」を無効化する
            if (!openButton.disabled) {
              openButton.textContent = "開く"; // ボタンのテキストをリセット
              openButton.style.display = "none"; // 「開く」ボタンを非表示
              openButton.disabled = true; // 「開く」ボタンを無効化
            }
          } catch (error) {
            console.error("サブディレクトリの取得中にエラーが発生しました:", error);
            openButton.textContent = "開く"; // エラー時にボタンをリセット
            openButton.disabled = false;
            openButton.style.display = "inline-block"; // 「開く」ボタンを再表示
            closeButton.style.display = "none"; // 「閉じる」ボタンを非表示
          }
        });

        // 「閉じる」の動作
        closeButton.addEventListener("click", () => {
          const subList = listItem.querySelector("ul");
          if (subList) {
            subList.remove(); // サブディレクトリを削除
          }
          openButton.textContent = "開く"; // ボタンのテキストをリセット
          openButton.disabled = false; // 「開く」ボタンを有効化
          openButton.style.display = "inline-block"; // 「開く」ボタンを再表示
          closeButton.style.display = "none"; // 「閉じる」ボタンを非表示
        });

        listItem.appendChild(addButton);
        listItem.appendChild(openButton);
        listItem.appendChild(closeButton);
        listItem.appendChild(document.createTextNode(dir.name));
        parentElement.appendChild(listItem);
    });
    } else {
      alert(`エラー: ${data.message}`);
    }
  } catch (error) {
    if (isPageNavigating) {
      console.warn("ディレクトリ取得中にページ遷移が発生したので、エラーを無視します。");
    } else {
      console.error("ディレクトリの取得中にエラーが発生しました:", error);
    }
  }
}
