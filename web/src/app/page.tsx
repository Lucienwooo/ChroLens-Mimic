import React from 'react';
import styles from './page.module.css';

export default function Home() {
  return (
    <main className={styles.main}>
      <h1>ChroLens Mimic</h1>
      <p className={styles.subtitle}>輕量級 Windows 巨集錄製與回放工具</p>

      <section className={styles.features}>
        <h2>核心功能</h2>

        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <h3>🎮 錄製與回放</h3>
            <ul>
              <li>錄製滑鼠和鍵盤操作</li>
              <li>支援暫停/繼續功能</li>
              <li>多種回放速度設定（1x-10x）</li>
              <li>智能視窗定位</li>
              <li>滑鼠模式與視窗模式切換</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>📝 腳本編輯器</h3>
            <ul>
              <li>文字指令式編輯器</li>
              <li>圖片辨識功能（支援pic命名）</li>
              <li>OCR文字辨識</li>
              <li>條件判斷與迴圈</li>
              <li>變數系統（v2.7.1+）</li>
              <li>語法高亮與自動完成</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>⚙️ 進階功能</h3>
            <ul>
              <li>多腳本管理</li>
              <li>快捷鍵設定</li>
              <li>排程執行</li>
              <li>MiniMode簡化介面</li>
              <li>腳本合併功能</li>
              <li>自動備份機制</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>🌍 國際化支援</h3>
            <ul>
              <li>繁體中文（預設）</li>
              <li>English（v2.7.3+完整支援）</li>
              <li>日本語（語言套件）</li>
              <li>可擴展語言系統</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>🖼️ 圖片辨識（v2.6.7+）</h3>
            <ul>
              <li>支援任意pic開頭命名</li>
              <li>辨識時顯示邊框</li>
              <li>範圍辨識（限定搜尋區域）</li>
              <li>組合參數使用</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>📋 剪貼簿操作（v2.7.3+）</h3>
            <ul>
              <li>複製到剪貼簿</li>
              <li>從剪貼簿讀取</li>
              <li>清空剪貼簿</li>
              <li>支援文字和圖片</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>🖥️ 視窗操作（v2.7.3+）</h3>
            <ul>
              <li>取得視窗標題</li>
              <li>設定視窗大小</li>
              <li>最小化/最大化/還原</li>
              <li>切換視窗</li>
              <li>取得視窗位置</li>
            </ul>
          </div>

          <div className={styles.featureCard}>
            <h3>📸 螢幕擷取（v2.7.3+）</h3>
            <ul>
              <li>截圖全螢幕</li>
              <li>截圖指定區域</li>
              <li>截圖指定視窗</li>
              <li>支援自動儲存</li>
            </ul>
          </div>
        </div>
      </section>

      <section className={styles.quickStart}>
        <h2>快速開始</h2>
        <ol>
          <li>下載並解壓縮 ChroLens_Mimic</li>
          <li>執行 ChroLens_Mimic.exe</li>
          <li>點擊「開始錄製」(F10) 開始錄製操作</li>
          <li>完成後點擊「停止」(F9)</li>
          <li>點擊「回放」(F12) 重播動作</li>
        </ol>
      </section>

      <section className={styles.useCases}>
        <h2>使用情境</h2>
        <div className={styles.caseGrid}>
          <div className={styles.caseCard}>
            <h3>💼 辦公自動化</h3>
            <p>Excel表格批次複製貼上、重複性表單填寫、檔案批次處理</p>
          </div>
          <div className={styles.caseCard}>
            <h3>🎮 遊戲輔助</h3>
            <p>定點採集、重複技能施放、自動尋路、簡單戰鬥輔助</p>
          </div>
          <div className={styles.caseCard}>
            <h3>🔧 系統維護</h3>
            <p>防止電腦進入待機、定時任務執行、自動備份</p>
          </div>
          <div className={styles.caseCard}>
            <h3>🧪 軟體測試</h3>
            <p>重複測試流程、UI自動化測試、迴歸測試</p>
          </div>
        </div>
      </section>

      <section className={styles.download}>
        <h2>下載與支援</h2>
        <p>
          <a href="https://github.com/Lucienwooo/ChroLens-Mimic/releases" target="_blank" rel="noopener noreferrer">
            📥 GitHub Releases - 下載最新版本
          </a>
        </p>
        <p>
          <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer">
            💬 Discord 社群 - 問題討論與建議
          </a>
        </p>
        <p>
          <a href="https://ko-fi.com/B0B51FBVA8" target="_blank" rel="noopener noreferrer">
            ☕ Ko-fi - 支持作者
          </a>
        </p>
        <p>
          <a href="/tutorial">
            📚 使用教學 - 從零開始學習 ChroLens Mimic
          </a>
        </p>
      </section>

      <section className={styles.version}>
        <h2>最新版本</h2>
        <h3>v2.7.4 - 編輯器修復與多螢幕支援</h3>
        <ul>
          <li>🐛 修復腳本編輯器視窗層級問題</li>
          <li>🎯 編輯器開啟後正確顯示在最上層並獲得焦點</li>
          <li>🖥️ 圖片辨識截圖功能支援所有螢幕</li>
          <li>🖱️ 左鍵/右鍵座標捕捉功能支援多螢幕環境</li>
          <li>📐 範圍選擇器支援跨螢幕操作</li>
        </ul>
      </section>
    </main>
  );
}
