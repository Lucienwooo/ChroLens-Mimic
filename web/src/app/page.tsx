import React from 'react';
import styles from './page.module.css';
import VideoPreview from '../components/VideoPreview';

interface FeatureCard {
  title: string;
  youtubeId?: string;
  videoSrc?: string;
  thumbnail?: string;
  features: string[];
}

const featureCards: FeatureCard[] = [
  {
    title: '🎮 錄製與回放',
    youtubeId: 'waHPYnjPwbM',
    features: [
      '錄製滑鼠和鍵盤操作',
      '支援暫停/繼續功能',
      '多種回放速度設定（1x–10x）',
      '智能視窗定位',
      '滑鼠模式與視窗模式切換',
    ],
  },
  {
    title: '📝 腳本編輯器',
    features: [
      '文字指令式編輯器',
      '圖片辨識功能（支援 pic 命名）',
      'OCR 文字辨識',
      '條件判斷與迴圈',
      '變數系統（v2.7.1+）',
      '語法高亮與自動完成',
    ],
  },
  {
    title: '⚙️ 進階功能',
    features: [
      '多腳本管理',
      '快捷鍵設定',
      '排程執行',
      'MiniMode 簡化介面',
      '腳本合併功能',
      '自動備份機制',
    ],
  },
  {
    title: '🌍 國際化支援',
    features: [
      '繁體中文（預設）',
      'English（v2.7.3+ 完整支援）',
      '日本語（語言套件）',
      '可擴展語言系統',
    ],
  },
  {
    title: '🖼️ 圖片辨識（v2.6.7+）',
    features: [
      '支援任意 pic 開頭命名',
      '辨識時顯示邊框',
      '範圍辨識（限定搜尋區域）',
      '組合參數使用',
    ],
  },
  {
    title: '📋 剪貼簿操作（v2.7.3+）',
    features: [
      '複製到剪貼簿',
      '從剪貼簿讀取',
      '清空剪貼簿',
      '支援文字和圖片',
    ],
  },
  {
    title: '🖥️ 視窗操作（v2.7.3+）',
    features: [
      '取得視窗標題',
      '設定視窗大小',
      '最小化/最大化/還原',
      '切換視窗',
      '取得視窗位置',
    ],
  },
  {
    title: '📸 螢幕擷取（v2.7.3+）',
    features: [
      '截圖全螢幕',
      '截圖指定區域',
      '截圖指定視窗',
      '支援自動儲存',
    ],
  },
];

export default function Home() {
  return (
    <main className={styles.main}>

      {/* ── Hero ── */}
      <div className={styles.hero}>
        <h1>ChroLens Mimic</h1>
        <p className={styles.heroSubtitle}>
          輕量級 Windows 巨集錄製與回放工具 — 透過文字腳本實現強大的自動化
        </p>
        <div className={styles.heroBadges}>
          <span className="badge">v2.7.5</span>
          <span className="badge badge-green">Windows 10/11</span>
          <span className="badge">免費開源</span>
        </div>
        <div className={styles.heroActions}>
          <a
            href="https://github.com/Lucienwooo/ChroLens-Mimic/releases"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.btnPrimary}
          >
            📥 下載最新版本
          </a>
          <a href="/tutorial" className={styles.btnSecondary}>
            📚 快速上手指南
          </a>
        </div>
      </div>

      {/* ── Core Features ── */}
      <section className={styles.section}>
        <h2>核心功能</h2>
        <div className={styles.featureGrid}>
          {featureCards.map((card, index) => (
            <div key={index} className={styles.featureCard}>
              {(card.youtubeId || card.videoSrc || card.thumbnail) && (
                <VideoPreview
                  youtubeId={card.youtubeId}
                  videoSrc={card.videoSrc}
                  thumbnail={card.thumbnail}
                  title={card.title}
                />
              )}
              <h3>{card.title}</h3>
              <ul>
                {card.features.map((feature, i) => (
                  <li key={i}>{feature}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ── Quick Start ── */}
      <section className={`${styles.section} ${styles.quickStart}`}>
        <h2>⚡ 快速開始</h2>
        <ol>
          <li>從 GitHub Releases 下載並解壓縮 <code>ChroLens_Mimic</code></li>
          <li>執行 <code>ChroLens_Mimic.exe</code>（建議以系統管理員身份執行）</li>
          <li>按 <kbd>F10</kbd> 開始錄製滑鼠 &amp; 鍵盤操作</li>
          <li>按 <kbd>F9</kbd> 停止錄製</li>
          <li>按 <kbd>F12</kbd> 回放錄製的動作</li>
        </ol>
      </section>

      {/* ── Use Cases ── */}
      <section className={styles.section}>
        <h2>使用情境</h2>
        <div className={styles.caseGrid}>
          <div className={styles.caseCard}>
            <h3>💼 辦公自動化</h3>
            <p>Excel 表格批次複製貼上、重複性表單填寫、檔案批次處理</p>
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
            <p>重複測試流程、UI 自動化測試、迴歸測試</p>
          </div>
        </div>
      </section>

      {/* ── Download & Links ── */}
      <section className={`${styles.section} ${styles.download}`}>
        <h2>下載與社群</h2>
        <ul className={styles.linkList}>
          <li>
            <a href="https://github.com/Lucienwooo/ChroLens-Mimic/releases" target="_blank" rel="noopener noreferrer">
              <span>📥</span> GitHub Releases — 下載最新版本
            </a>
          </li>
          <li>
            <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer">
              <span>💬</span> Discord 社群 — 問題討論與建議
            </a>
          </li>
          <li>
            <a href="https://ko-fi.com/B0B51FBVA8" target="_blank" rel="noopener noreferrer">
              <span>☕</span> Ko-fi — 支持作者開發
            </a>
          </li>
          <li>
            <a href="/tutorial">
              <span>📚</span> 使用教學 — 從零開始學習 ChroLens Mimic
            </a>
          </li>
        </ul>
      </section>

      {/* ── Latest Version ── */}
      <section className={`${styles.section} ${styles.version}`}>
        <h2>最新版本</h2>
        <h3>v2.7.5 — 按鍵系統全面增強</h3>
        <ul>
          <li>⌨️ 完美支援所有按鍵類型（Alt、Ctrl、Shift 等修飾鍵）</li>
          <li>🎮 遊戲按鍵完全支援（Alt 跳躍/攻擊、組合技等）</li>
          <li>🔧 按鍵名稱自動標準化，處理不同鍵盤庫差異</li>
          <li>🛡️ 防卡鍵機制，執行結束自動釋放所有按鍵</li>
          <li>📝 術語優化：「回放」改為「執行」（更直觀）</li>
        </ul>
      </section>

    </main>
  );
}
