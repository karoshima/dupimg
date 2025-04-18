// フォームの送信イベントをリッスン
const settingsForm = document.getElementById("settings-form") as HTMLFormElement;

settingsForm.addEventListener("submit", async (event: Event) => {
  event.preventDefault(); // フォームのデフォルト動作を無効化

  const formData = new FormData(settingsForm);
  try {
    const response = await fetch("/settings", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }

    const result: { directory: string; algorithm: string; similarity: string } = await response.json();
    console.log(result); // サーバーからのレスポンスを確認
    alert(`ディレクトリ: ${result.directory}, アルゴリズム: ${result.algorithm}, 類似度: ${result.similarity}`);
  } catch (error) {
    console.error("エラーが発生しました:", error);
    alert("エラーが発生しました。詳細はコンソールを確認してください。");
  }
});
