/**
 * @jest-environment jsdom
 */

import { initialize, showPopup, hidePopup, fetchDirectories } from '../../static/ts/settings';

describe('ディレクトリ選択機能のテスト', () => {
  let directoryPopup: HTMLDivElement;
  let directoryList: HTMLUListElement;

  beforeEach(() => {
    // テスト用の DOM をセットアップ
    document.body.innerHTML = `
    <form id="settings-form">
      <input type="text" id="directory" />
      <button type="button" id="add-directory">追加</button>
      <button type="button" id="select-directory">ディレクトリを選択</button>
      <ul id="selected-directories"></ul>
    </form>
    <div id="directory-popup" style="display: none;">
      <ul id="directory-list"></ul>
      <button id="close-popup">閉じる</button>
    </div>
  `;
    directoryPopup = document.getElementById('directory-popup') as HTMLDivElement;
    directoryList = document.getElementById('directory-list') as HTMLUListElement;
    initialize();
  });

  test('ポップアップを表示する', () => {
    showPopup();
    expect(directoryPopup.style.display).toBe('block');
  });

  test('ポップアップを非表示にする', () => {
    directoryPopup.style.display = 'block'; // 初期状態を表示に設定
    hidePopup();
    expect(directoryPopup.style.display).toBe('none');
  });

  test('ディレクトリ構造を取得して表示する', async () => {
    // モックの API レスポンス
    const mockResponse = {
      status: 'success',
      directories: [
        { name: 'dir1', path: '/dir1' },
        { name: 'dir2', path: '/dir2' },
      ],
    };

    // fetch をモック
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockResponse),
      })
    ) as jest.Mock;

    await fetchDirectories('/', directoryList);

    // ディレクトリリストが正しく生成されているか確認
    expect(directoryList.children.length).toBe(2);
    expect(directoryList.children[0].textContent).toBe('dir1');
    expect(directoryList.children[1].textContent).toBe('dir2');
  });
});
