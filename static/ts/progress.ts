async function fetchProgressData(): Promise<void> {
  try {
    const response = await fetch("/progress/data");
    if (!response.ok) {
      throw new Error(`HTTPエラー: ${response.status}`);
    }
    const data = await response.json();

    // 全体の進捗を表示
    document.getElementById("time")!.textContent = `現在時刻: ${data.time}`;
    document.getElementById("overall-progress")!.textContent = `全体進捗: ${data.progress}%`;
    document.getElementById("status")!.textContent = `ステータス: ${data.status}`;
    document.getElementById("message")!.textContent = `メッセージ: ${data.message}`;

    // 各ステップの進捗を表示
    const stepsContainer = document.getElementById("steps")!;
    stepsContainer.innerHTML = ""; // 既存の内容をクリア
    data.steps.forEach((step: any) => {
      const stepElement = document.createElement("div");
      stepElement.className = "step";
      stepElement.innerHTML = `
        <div class="name">${step.name}</div>
        <div class="progress">進捗: ${step.progress}% (${step.status})</div>
      `;
      stepsContainer.appendChild(stepElement);
    });
  } catch (error) {
    console.error("進捗データの取得中にエラーが発生しました:", error);
  }
}

// 毎秒ごとに進捗データを取得
setInterval(fetchProgressData, 1000);
