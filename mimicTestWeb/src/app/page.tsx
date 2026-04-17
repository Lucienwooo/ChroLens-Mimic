import React from 'react';
import styles from './page.module.css';
import VideoPreview from '@/components/VideoPreview';

interface FeatureCard {
  title: string;
  subtitle: string;
  description: string;
  badge: string;
  icon: string;
  features: string[];
  color: string;
}

const featureCards: FeatureCard[] = [
  {
    title: '功能強大的錄製與回放',
    subtitle: '智慧型操作同步',
    description: '輕鬆記錄滑鼠點擊與鍵盤輸入，並以亞毫秒級的精度重現。支援多段錄製組合與即時微調功能。',
    badge: '✦ 主打功能',
    icon: 'videocam',
    color: '#4A3728', // 深棕色 - 權威感
    features: [
      '毫秒級高精度錄製',
      '跨視窗自動定位',
      '支援錄製中途暫停',
      '全方位鍵位捕捉'
    ],
  },
  {
    title: '指令式腳本編輯器',
    subtitle: '視覺化與邏輯並行',
    description: '無需深厚開發背景也能掌握。透過簡潔指令實現條件判斷、循環、與自訂變數管理。',
    badge: '高效作業',
    icon: 'terminal',
    color: '#E6D5C3', // 奶茶色 - 清新感
    features: [
      '快速語法高亮',
      '多腳本管理系統',
      '支援模組化引用',
      '錯誤偵測與修復'
    ],
  },
  {
    title: '圖片與文字辨識系統',
    subtitle: '讓自動化擁有一雙亮眼',
    description: '結合 OpenCV 與先進 OCR，自動尋找螢幕上的特定影像或文字。即使視窗位置變動也能精準辨識。',
    badge: 'AI 技術支援',
    icon: 'filter_center_focus',
    color: '#A68966', // 琥珀金 - 質感
    features: [
      '不限格式區域辨識',
      '動態物件追蹤',
      '支援透明底圖比對',
      '多語系文字偵測'
    ],
  },
  {
    title: '進階自動化解決方案',
    subtitle: '讓電腦為您全時工作',
    description: '具備計數器、計時器與視窗管理核心。無論是日常辦公還是複雜模擬，皆可一站式搞定。',
    badge: '專業首選',
    icon: 'settings_input_component',
    color: '#CABFA3', // 灰金色 - 穩定感
    features: [
      '變數運算與跳轉',
      '視窗大小精準調整',
      '剪貼簿管理支援',
      '自動重啟保護機制'
    ],
  },
];


export default function Home() {
  return (
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

          {/* Product Grid - Inspired by vvcoffee2024 */}
          <section className={styles.productSection}>
            <div className={styles.sectionHeader}>
               <p className={styles.sectionTag}>服務項目</p>
               <h2 className={styles.sectionTitle}>為您量身打造的自動化</h2>
               <p className={styles.sectionDesc}>多款核心功能，適合不同場景與需求，也歡迎諮詢其他客製化自動化方案</p>
            </div>
            
            <div className={styles.productGrid}>
              {featureCards.map((card, index) => (
                <div key={index} className={styles.productCard}>
                  <div className={styles.cardTop} style={{ backgroundColor: card.color }}>
                    <span className={`material-symbols-outlined ${styles.productIcon}`}>
                      {card.icon}
                    </span>
                  </div>
                  <div className={styles.cardBottom}>
                    <div className={styles.badge}>{card.badge}</div>
                    <h3 className={styles.productTitle}>{card.title}</h3>
                    <p className={styles.productSubtitle}>{card.subtitle}</p>
                    <p className={styles.productDescription}>{card.description}</p>
                    <div className={styles.tagList}>
                      {card.features.map((f, i) => (
                        <span key={i} className={styles.tagPill}>
                          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>check_circle</span>
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
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

          <footer className={styles.footer}>
            <p>© 2026 ChroLens Mimic - Designed for Efficiency</p>
          </footer>
        </div>
      </main>
  );
}
