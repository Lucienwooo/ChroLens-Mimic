'use client';

import React from 'react';
import styles from '../page.module.css';

// YouTube 嵌入元件
const YouTubeEmbed = ({ videoId, title }: { videoId: string; title: string }) => (
  <div className={styles.videoContainer}>
    <iframe
      src={`https://www.youtube.com/embed/${videoId}`}
      title={title}
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowFullScreen
    />
  </div>
);

export default function BasicTutorialPage() {
  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1>📖 基礎使用教學</h1>
        <p>從零開始學習 ChroLens Mimic</p>
      </div>

      <nav className={styles.nav}>
        <a href="/tutorial">← 返回教學首頁</a>
        <a href="/tutorial/advanced">進階教學</a>
        <a href="/tutorial/examples">範例腳本</a>
      </nav>

      <section className={styles.tutorialList}>
        {/* 下載與安裝 */}
        <article className={styles.stepCard} style={{ borderColor: '#4ec9b0' }}>
          <div className={styles.stepContent} style={{ padding: '1.5rem' }}>
            <h2 style={{ color: '#4ec9b0', marginTop: 0 }}>📥 下載與安裝</h2>
            
            <h4>系統需求</h4>
            <ul>
              <li>Windows 10 或更高版本</li>
              <li>建議 4GB RAM 以上</li>
              <li>需要管理員權限（用於全局快捷鍵）</li>
            </ul>

            <h4>安裝步驟</h4>
            <ol>
              <li>
                前往 <a href="https://github.com/Lucienwooo/ChroLens-Mimic/releases" target="_blank" rel="noopener noreferrer">GitHub Releases 頁面</a>
              </li>
              <li>下載最新版本的 <code>ChroLens_Mimic_vX.X.X.zip</code></li>
              <li>解壓縮到任意目錄（建議非中文路徑）</li>
              <li>執行 <code>ChroLens_Mimic.exe</code></li>
            </ol>

            <div className={styles.tipBox}>
              <strong>💡 提示：</strong>
              如果 Windows 顯示「Windows 已保護您的電腦」，請點擊「更多資訊」→「仍要執行」
            </div>

            {/* YouTube 影片預留位置 */}
            <div className={styles.videoPlaceholder}>
              <p>📹 安裝教學影片（即將上傳）</p>
              {/* <YouTubeEmbed videoId="YOUR_VIDEO_ID" title="安裝教學" /> */}
            </div>
          </div>
        </article>

        {/* 介面介紹 */}
        <article className={styles.stepCard} style={{ borderColor: '#58a6ff' }}>
          <div className={styles.stepContent} style={{ padding: '1.5rem' }}>
            <h2 style={{ color: '#58a6ff', marginTop: 0 }}>🖥️ 介面介紹</h2>
            
            <h4>主介面區域</h4>
            <ul>
              <li><strong>上方控制列</strong>：錄製、暫停、停止、回放按鈕</li>
              <li><strong>參數設定區</strong>：回放速度、重複次數、時間設定</li>
              <li><strong>腳本選單</strong>：選擇、重新命名已儲存的腳本</li>
              <li><strong>左側頁籤</strong>：日誌顯示、腳本編輯器、腳本設定、整體設定</li>
            </ul>

            <h4>重要設定說明</h4>
            <table className={styles.hotkeyTable}>
              <thead>
                <tr>
                  <th>設定項目</th>
                  <th>說明</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>回放速度</td>
                  <td>100 = 正常速度，200 = 2倍速</td>
                </tr>
                <tr>
                  <td>重複次數</td>
                  <td>0 = 無限重複</td>
                </tr>
                <tr>
                  <td>重複時間</td>
                  <td>格式 HH:MM:SS，優先於次數</td>
                </tr>
                <tr>
                  <td>重複間隔</td>
                  <td>每次回放之間的等待時間</td>
                </tr>
                <tr>
                  <td>滑鼠模式</td>
                  <td>勾選 = 控制真實滑鼠</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        {/* 快捷鍵 */}
        <article className={styles.stepCard} style={{ borderColor: '#c586c0' }}>
          <div className={styles.stepContent} style={{ padding: '1.5rem' }}>
            <h2 style={{ color: '#c586c0', marginTop: 0 }}>⌨️ 快捷鍵操作</h2>
            
            <h4>預設快捷鍵</h4>
            <table className={styles.hotkeyTable}>
              <thead>
                <tr>
                  <th>功能</th>
                  <th>快捷鍵</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>開始錄製</td>
                  <td><kbd>F10</kbd></td>
                </tr>
                <tr>
                  <td>暫停/繼續</td>
                  <td><kbd>F11</kbd></td>
                </tr>
                <tr>
                  <td>停止錄製/回放</td>
                  <td><kbd>F9</kbd></td>
                </tr>
                <tr>
                  <td>開始回放</td>
                  <td><kbd>F12</kbd></td>
                </tr>
                <tr>
                  <td>切換 MiniMode</td>
                  <td><kbd>Alt</kbd> + <kbd>`</kbd></td>
                </tr>
                <tr>
                  <td>強制停止</td>
                  <td><kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>Z</kbd></td>
                </tr>
              </tbody>
            </table>

            <div className={styles.tipBox}>
              <strong>💡 提示：</strong>
              快捷鍵可在「整體設定」頁籤中自訂修改
            </div>
          </div>
        </article>

        {/* 第一個腳本 */}
        <article className={styles.stepCard} style={{ borderColor: '#3fb950' }}>
          <div className={styles.stepContent} style={{ padding: '1.5rem' }}>
            <h2 style={{ color: '#3fb950', marginTop: 0 }}>🎬 錄製第一個腳本</h2>
            
            <h4>快速開始</h4>
            <ol>
              <li>按 <kbd>F10</kbd> 開始錄製</li>
              <li>執行你想要自動化的操作（滑鼠點擊、鍵盤輸入）</li>
              <li>按 <kbd>F9</kbd> 停止錄製</li>
              <li>腳本會自動儲存到 <code>scripts/</code> 資料夾</li>
            </ol>

            <h4>回放腳本</h4>
            <ol>
              <li>從「腳本選單」選擇要回放的腳本</li>
              <li>設定回放參數（速度、重複次數等）</li>
              <li>按 <kbd>F12</kbd> 開始回放</li>
              <li>按 <kbd>F9</kbd> 可隨時停止</li>
            </ol>

            <div className={styles.warningBox}>
              <strong>⚠️ 注意：</strong>
              回放時請勿移動滑鼠，否則可能影響腳本執行準確性
            </div>

            {/* YouTube 影片預留位置 */}
            <div className={styles.videoPlaceholder}>
              <p>📹 錄製教學影片（即將上傳）</p>
            </div>
          </div>
        </article>

        {/* MiniMode */}
        <article className={styles.stepCard} style={{ borderColor: '#dcdcaa' }}>
          <div className={styles.stepContent} style={{ padding: '1.5rem' }}>
            <h2 style={{ color: '#dcdcaa', marginTop: 0 }}>📱 MiniMode 迷你模式</h2>
            
            <p>MiniMode 是一個精簡的控制介面，適合在回放時使用。</p>

            <h4>功能特點</h4>
            <ul>
              <li>小巧視窗，不佔用螢幕空間</li>
              <li>顯示當前狀態和時間</li>
              <li>快速控制錄製/回放</li>
              <li>可設置「自動切換」在錄製/回放時自動進入</li>
            </ul>

            <h4>如何使用</h4>
            <ol>
              <li>點擊主介面的「MiniMode」按鈕</li>
              <li>或按 <kbd>Alt</kbd> + <kbd>`</kbd> 快捷鍵切換</li>
              <li>勾選「自動切換」可在錄製/回放時自動進入 MiniMode</li>
            </ol>
          </div>
        </article>
      </section>

      <section className={styles.nextSteps}>
        <h2>🚀 下一步</h2>
        <div className={styles.nextGrid}>
          <a href="/tutorial/advanced" className={styles.nextCard}>
            <h3>進階功能</h3>
            <p>圖片辨識、條件判斷、變數</p>
          </a>
          <a href="/tutorial/examples" className={styles.nextCard}>
            <h3>範例腳本</h3>
            <p>實用的自動化範例</p>
          </a>
          <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>加入社群</h3>
            <p>提問與交流</p>
          </a>
        </div>
      </section>
    </main>
  );
}
