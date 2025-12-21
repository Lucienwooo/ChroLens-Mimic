'use client';

import React, { useState } from 'react';
import styles from './page.module.css';

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

// 步驟卡片元件
const StepCard = ({ 
  step, 
  title, 
  description, 
  children,
  isExpanded,
  onToggle
}: { 
  step: number;
  title: string;
  description: string;
  children?: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
}) => (
  <div className={`${styles.stepCard} ${isExpanded ? styles.expanded : ''}`}>
    <div className={styles.stepHeader} onClick={onToggle}>
      <div className={styles.stepNumber}>{step}</div>
      <div className={styles.stepInfo}>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <div className={styles.expandIcon}>{isExpanded ? '▲' : '▼'}</div>
    </div>
    {isExpanded && (
      <div className={styles.stepContent}>
        {children}
      </div>
    )}
  </div>
);

// 進度指示器
const ProgressIndicator = ({ current, total }: { current: number; total: number }) => (
  <div className={styles.progressContainer}>
    <div className={styles.progressBar}>
      <div 
        className={styles.progressFill} 
        style={{ width: `${(current / total) * 100}%` }}
      />
    </div>
    <span className={styles.progressText}>{current} / {total} 完成</span>
  </div>
);

export default function TutorialPage() {
  const [expandedStep, setExpandedStep] = useState<number | null>(1);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (step: number) => {
    setExpandedStep(expandedStep === step ? null : step);
  };

  const markComplete = (step: number) => {
    setCompletedSteps(prev => new Set(Array.from(prev).concat([step])));
  };

  const tutorials = [
    {
      step: 1,
      title: '下載與安裝',
      description: '取得 ChroLens Mimic 並完成基本設定',
      content: (
        <>
          <h4>步驟說明</h4>
          <ol>
            <li>前往 <a href="https://github.com/Lucienwooo/ChroLens-Mimic/releases" target="_blank" rel="noopener noreferrer">GitHub Releases</a> 下載最新版本</li>
            <li>解壓縮 ZIP 檔案到任意目錄</li>
            <li>執行 <code>ChroLens_Mimic.exe</code></li>
            <li>若系統提示安全性警告，請點擊「仍要執行」</li>
          </ol>

          <div className={styles.tipBox}>
            <strong>💡 提示：</strong>建議以管理員身份執行以獲得完整功能
          </div>

          {/* 預留 YouTube 影片位置 */}
          <div className={styles.videoPlaceholder}>
            <p>📹 安裝教學影片（即將上傳）</p>
            {/* <YouTubeEmbed videoId="YOUR_VIDEO_ID" title="安裝教學" /> */}
          </div>

          <button 
            className={styles.completeBtn}
            onClick={() => markComplete(1)}
          >
            ✓ 我已完成此步驟
          </button>
        </>
      )
    },
    {
      step: 2,
      title: '錄製第一個腳本',
      description: '學習基本的滑鼠和鍵盤錄製',
      content: (
        <>
          <h4>快速開始</h4>
          <ol>
            <li>點擊「<strong>開始錄製</strong>」按鈕或按 <kbd>F10</kbd></li>
            <li>執行你想要自動化的滑鼠和鍵盤操作</li>
            <li>點擊「<strong>停止</strong>」按鈕或按 <kbd>F9</kbd> 結束錄製</li>
          </ol>

          <h4>快捷鍵一覽</h4>
          <table className={styles.hotkeyTable}>
            <thead>
              <tr>
                <th>功能</th>
                <th>快捷鍵</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>開始錄製</td><td><kbd>F10</kbd></td></tr>
              <tr><td>暫停/繼續</td><td><kbd>F11</kbd></td></tr>
              <tr><td>停止</td><td><kbd>F9</kbd></td></tr>
              <tr><td>回放</td><td><kbd>F12</kbd></td></tr>
              <tr><td>強制停止</td><td><kbd>Ctrl+Alt+Z</kbd></td></tr>
            </tbody>
          </table>

          <div className={styles.videoPlaceholder}>
            <p>📹 錄製教學影片（即將上傳）</p>
          </div>

          <button 
            className={styles.completeBtn}
            onClick={() => markComplete(2)}
          >
            ✓ 我已完成此步驟
          </button>
        </>
      )
    },
    {
      step: 3,
      title: '回放與速度調整',
      description: '執行錄製的腳本並調整回放參數',
      content: (
        <>
          <h4>回放設定</h4>
          <ul>
            <li><strong>回放速度</strong>：1-1000%，100 為正常速度</li>
            <li><strong>重複次數</strong>：設定執行次數，0 為無限重複</li>
            <li><strong>重複時間</strong>：設定總運作時間（格式：HH:MM:SS）</li>
            <li><strong>重複間隔</strong>：每次執行之間的等待時間</li>
          </ul>

          <div className={styles.codeBlock}>
            <pre>{`# 範例：每次執行間隔 5 秒，重複 10 次
重複次數: 10
重複間隔: 00:00:05`}</pre>
          </div>

          <div className={styles.warningBox}>
            <strong>⚠️ 注意：</strong>回放時請勿移動滑鼠，否則可能影響腳本執行
          </div>

          <button 
            className={styles.completeBtn}
            onClick={() => markComplete(3)}
          >
            ✓ 我已完成此步驟
          </button>
        </>
      )
    },
    {
      step: 4,
      title: '儲存與載入腳本',
      description: '管理你的自動化腳本',
      content: (
        <>
          <h4>腳本管理</h4>
          <ul>
            <li>錄製完成後自動儲存到 <code>scripts/</code> 資料夾</li>
            <li>檔案格式為 JSON，可手動編輯</li>
            <li>從下拉選單選擇已儲存的腳本</li>
            <li>使用「重新命名」功能給腳本取一個好記的名字</li>
          </ul>

          <h4>腳本設定頁面</h4>
          <p>在「腳本設定」頁籤可以：</p>
          <ul>
            <li>為腳本設定專屬快捷鍵</li>
            <li>刪除不需要的腳本</li>
            <li>開啟腳本資料夾</li>
            <li>合併多個腳本</li>
          </ul>

          <button 
            className={styles.completeBtn}
            onClick={() => markComplete(4)}
          >
            ✓ 我已完成此步驟
          </button>
        </>
      )
    },
    {
      step: 5,
      title: '使用腳本編輯器',
      description: '學習文字指令編輯器的基本操作',
      content: (
        <>
          <h4>開啟編輯器</h4>
          <p>點擊左側選單的「腳本編輯器」，即可開啟文字指令編輯器。</p>

          <h4>常用指令</h4>
          <div className={styles.codeBlock}>
            <pre>{`# 這是註解
#我的標籤

>移動至(500,300), 延遲0ms, T=0s000
>左鍵點擊, 延遲50ms, T=0s000
>按escape, 延遲50ms, T=0s000
>延遲1000ms, T=0s000

# 分支跳轉
>>#成功標籤
>>>#失敗標籤`}</pre>
          </div>

          <h4>編輯器功能</h4>
          <ul>
            <li>語法高亮（VS Code 風格）</li>
            <li>快速指令按鈕</li>
            <li>圖形模式（Workflow 流程圖）</li>
            <li>截圖辨識工具</li>
          </ul>

          <button 
            className={styles.completeBtn}
            onClick={() => markComplete(5)}
          >
            ✓ 我已完成此步驟
          </button>
        </>
      )
    }
  ];

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1>📚 ChroLens Mimic 使用教學</h1>
        <p>跟著步驟學習，快速上手自動化工具</p>
        <ProgressIndicator current={completedSteps.size} total={tutorials.length} />
      </div>

      <nav className={styles.nav}>
        <a href="/">← 返回首頁</a>
        <a href="/tutorial/basic">基礎教學</a>
        <a href="/tutorial/advanced">進階教學</a>
        <a href="/tutorial/examples">範例腳本</a>
      </nav>

      <section className={styles.tutorialList}>
        {tutorials.map((tutorial) => (
          <StepCard
            key={tutorial.step}
            step={tutorial.step}
            title={tutorial.title}
            description={tutorial.description}
            isExpanded={expandedStep === tutorial.step}
            onToggle={() => toggleStep(tutorial.step)}
          >
            {tutorial.content}
          </StepCard>
        ))}
      </section>

      <section className={styles.nextSteps}>
        <h2>🚀 下一步</h2>
        <div className={styles.nextGrid}>
          <a href="/tutorial/advanced" className={styles.nextCard}>
            <h3>進階功能</h3>
            <p>圖片辨識、OCR、條件判斷</p>
          </a>
          <a href="/tutorial/examples" className={styles.nextCard}>
            <h3>範例腳本</h3>
            <p>實用的自動化腳本範例</p>
          </a>
          <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>Discord 社群</h3>
            <p>加入社群討論問題</p>
          </a>
        </div>
      </section>
    </main>
  );
}
