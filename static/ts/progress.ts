// 時刻を取得して画面に表示する関数
async function fetchTime(): Promise<void> {
  try {
    const response = await fetch("/progress/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }
    const data = await response.json();
    const timeElement = document.getElementById("time");
    if (timeElement) {
      timeElement.textContent = `現在時刻: ${data.time}`;
    }
  } catch (error) {
    console.error("時刻の取得中にエラーが発生しました:", error);
  }
}

// 毎秒ごとに時刻を取得
setInterval(fetchTime, 1000);
