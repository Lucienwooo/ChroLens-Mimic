import React from 'react';
import styles from './page.module.css';
import VideoPreview from '@/components/VideoPreview';

interface FeatureCard {
  title: string;
  youtubeId?: string;
  videoSrc?: string;
  thumbnail?: string;
  features: string[];
  icon: string;
  size?: 'small' | 'medium' | 'large';
}

const featureCards: FeatureCard[] = [
  {
    title: '🎮 錄製與回放',
    youtubeId: 'waHPYnjPwbM',
    icon: 'gesture',
    size: 'large',
    features: [
      '錄製滑鼠和鍵盤操作',
      '支援暫停/繼續功能',
      '多種回放速度設定（1x–10x）',
      '智能視窗定位',
    ],
  },
  {
    title: '📝 腳本編輯器',
    icon: 'code_blocks',
    size: 'medium',
    features: [
      '文字指令式編輯器',
      '圖片辨識功能',
      'OCR 文字辨識',
      '條件判斷與迴圈',
    ],
  },
  {
    title: '🖼️ 圖片辨識',
    icon: 'image_search',
    size: 'small',
    features: [
      '支援任意 pic 開頭命名',
      '範圍辨識（限定搜尋區域）',
      '組合參數使用',
    ],
  },
  {
    title: '⚙️ 進階功能',
    icon: 'settings',
    size: 'small',
    features: [
      '多腳本管理',
      '快捷鍵設定',
      '排程執行',
    ],
  },
  {
    title: '📋 剪貼簿操作',
    icon: 'content_paste',
    size: 'small',
    features: [
      '複製到剪貼簿',
      '從剪貼簿讀取',
    ],
  },
  {
    title: '🖥️ 視窗操作',
    icon: 'window',
    size: 'small',
    features: [
      '設定視窗大小',
      '切換視窗',
    ],
  },
];

export default function Home() {
  return (
    <div className={styles.layout}>
      {/* --- Sidebar --- */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h1 className={styles.logo}>
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>terminal</span>
            Mimic
          </h1>
        </div>
        <nav className={styles.nav}>
          <a href="#" className={`${styles.navLink} ${styles.active}`}>
            <span className="material-symbols-outlined">dashboard</span>
            總覽
          </a>
          <a href="/tutorial" className={styles.navLink}>
            <span className="material-symbols-outlined">menu_book</span>
            教學
          </a>
          <a href="https://github.com/Lucienwooo/ChroLens-Mimic" target="_blank" rel="noopener noreferrer" className={styles.navLink}>
            <span className="material-symbols-outlined">code</span>
            GitHub
          </a>
        </nav>
        <div className={styles.sidebarFooter}>
          <div className={styles.statusBadge}>
            <div className={styles.pulse}></div>
            v2.7.8 Online
          </div>
        </div>
      </aside>

      {/* --- Main Content --- */}
      <main className={styles.main}>
        {/* Glow Effects */}
        <div className={styles.glowTop}></div>

        <div className={styles.container}>
          {/* Hero */}
          <section className={styles.hero}>
            <div className={styles.heroContent}>
              <h2 className={styles.heroTitle}>
                Automate the <br />
                <span className={styles.gradientText}>Unautomatable.</span>
              </h2>
              <p className={styles.heroSubtitle}>
                輕量級 Windows 巨集錄製與回放工具 — 透過文字腳本實現強大的自動化。
                錄製滑鼠和鍵盤操作，並以亞毫秒級的精度重現。
              </p>
              <div className={styles.heroActions}>
                <a
                  href="https://github.com/Lucienwooo/ChroLens-Mimic/releases"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.btnPrimary}
                >
                  <span className="material-symbols-outlined">download</span>
                  下載最新版本
                </a>
              </div>
            </div>
          </section>

          {/* Bento Grid */}
          <section className={styles.bentoSection}>
            <div className={styles.bentoGrid}>
              {featureCards.map((card, index) => (
                <div 
                  key={index} 
                  className={`${styles.bentoCard} ${styles[(card.size || 'small') as keyof typeof styles]}`}
                >
                  <div className={styles.cardHeader}>
                    <span className={`material-symbols-outlined ${styles.cardIcon}`}>{card.icon}</span>
                    <h3>{card.title}</h3>
                  </div>
                  <ul className={styles.cardFeatures}>
                    {card.features.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                  {card.youtubeId && (
                    <div className={styles.cardVideo}>
                      <VideoPreview youtubeId={card.youtubeId} title={card.title} />
                    </div>
                  )}
                  {card.size === 'large' && (
                     <div className={styles.cardDecoration}>
                        <svg viewBox="0 0 400 200" className={styles.svgDecoration}>
                           <path d="M0 50H400 M0 100H400 M0 150H400 M50 0V200 M100 0V200 M150 0V200 M200 0V200 M250 0V200 M300 0V200 M350 0V200" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
                           <path d="M50 150 C 100 150, 150 50, 200 80 S 300 180, 350 50" fill="none" stroke="#00F0FF" strokeWidth="2" strokeLinecap="round" />
                           <circle cx="50" cy="150" r="4" fill="#0A0A0A" stroke="#00F0FF" strokeWidth="2" />
                           <circle cx="350" cy="50" r="4" fill="#00F0FF" />
                        </svg>
                     </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Quick Start Card */}
          <section className={styles.fullWidthSection}>
             <div className={styles.bentoCard}>
                <div className={styles.cardHeader}>
                   <span className="material-symbols-outlined">bolt</span>
                   <h3>快速開始</h3>
                </div>
                <div className={styles.quickStartGrid}>
                   <div className={styles.step}>
                      <span className={styles.stepNum}>1</span>
                      <p>下載並解壓縮 <code>ChroLens_Mimic</code></p>
                   </div>
                   <div className={styles.step}>
                      <span className={styles.stepNum}>2</span>
                      <p>執行 <code>ChroLens_Mimic.exe</code></p>
                   </div>
                   <div className={styles.step}>
                      <span className={styles.stepNum}>3</span>
                      <p>按 <kbd>F10</kbd> 錄製，按 <kbd>F12</kbd> 執行</p>
                   </div>
                </div>
             </div>
          </section>

        </div>
      </main>
      
      {/* --- Footer --- */}
      <footer className={styles.footer}>
         <p>© 2026 ChroLens Mimic - Designed for Efficiency</p>
      </footer>
    </div>
  );
}
