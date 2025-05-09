async function checkAndRedirect(): Promise<void> {
  try {
    const response = await fetch("/api/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }
    const data = await response.json();

    // 状態に応じてリダイレクト
    if (window.location.pathname !== data.page) {
      window.location.href = data.page;
    }
  } catch (error) {
    console.error("状態チェック中にエラーが発生しました:", error);
  }
}

// ページ読み込み時に状態をチェック
document.addEventListener("DOMContentLoaded", checkAndRedirect);
