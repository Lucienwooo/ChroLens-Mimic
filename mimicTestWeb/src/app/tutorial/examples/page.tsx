'use client';

import React, { useState } from 'react';
import styles from '../page.module.css';

// 範例腳本資料
const examples = [
  {
    id: 'office',
    category: '💼 辦公自動化',
    title: 'Excel 批次複製貼上',
    description: '自動從一個工作表複製資料到另一個工作表',
    code: `# Excel 批次複製貼上範例
# 假設已開啟 Excel 檔案

#開始
>按Ctrl,Home, 延遲50ms, T=0s000
>延遲500ms, T=0s000

#複製資料
>重複>10次, T=0s000
>按Ctrl,c, 延遲50ms, T=0s000
>延遲200ms, T=0s000
>按Ctrl,Tab, 延遲50ms, T=0s000
>延遲300ms, T=0s000
>按Ctrl,v, 延遲50ms, T=0s000
>延遲200ms, T=0s000
>按Ctrl,Tab, 延遲50ms, T=0s000
>延遲300ms, T=0s000
>按Down, 延遲50ms, T=0s000
>重複結束, T=0s000

>按Ctrl,s, 延遲50ms, T=0s000
>延遲1000ms, T=0s000
# 完成`,
    tips: [
      '執行前請確認 Excel 視窗已開啟並對焦',
      '根據實際資料量調整重複次數',
      '可加入錯誤處理避免卡住'
    ]
  },
  {
    id: 'game-farm',
    category: '🎮 遊戲輔助',
    title: '自動打怪腳本',
    description: '自動尋找怪物、攻擊、撿取戰利品',
    code: `# 自動打怪腳本範例
#初始化
>設定變數>擊殺數, 0, T=0s000
>設定變數>目標數, 100, T=0s000
>>#主循環

#主循環
>if變數>擊殺數, >=, 目標數, T=0s000
>>#任務完成
>>>#尋找怪物

#尋找怪物
>計時器>搜尋超時, 30秒後, T=0s000
>>#處理超時
>辨識>pic怪物, T=0s000
>>#發現怪物
>>>#移動尋找

#發現怪物
>重置計時器>搜尋超時, T=0s000
>左鍵點擊>pic怪物, T=0s000
>延遲500ms, T=0s000
>>#攻擊流程

#攻擊流程
>按1, 延遲50ms, T=0s000
>延遲800ms, T=0s000
>按2, 延遲50ms, T=0s000
>延遲1000ms, T=0s000
>辨識>pic怪物, T=0s000
>>#攻擊流程
>>>#怪物死亡

#怪物死亡
>變數加1>擊殺數, T=0s000
>延遲500ms, T=0s000
>重複>3次, T=0s000
>按z, 延遲50ms, T=0s000
>延遲200ms, T=0s000
>重複結束, T=0s000
>>#主循環

#移動尋找
>移動至(800,400), 延遲0ms, T=0s000
>左鍵點擊, 延遲50ms, T=0s000
>隨機延遲>1500ms,2500ms, T=0s000
>>#尋找怪物

#處理超時
>重置計時器>搜尋超時, T=0s000
>按m, 延遲50ms, T=0s000
>延遲1000ms, T=0s000
>>#主循環

#任務完成
>延遲1000ms, T=0s000
# 完成`,
    tips: [
      '需要先截取「怪物」圖片並命名為 pic怪物',
      '根據遊戲調整技能按鍵和延遲時間',
      '使用隨機延遲避免被偵測'
    ]
  },
  {
    id: 'anti-afk',
    category: '🔧 系統維護',
    title: '防止電腦待機',
    description: '定時移動滑鼠防止電腦進入休眠狀態',
    code: `# 防止電腦待機腳本
# 設定：無限重複，重複間隔 4 分鐘

#保持活動
>移動至(960,540), 延遲0ms, T=0s000
>延遲100ms, T=0s000
>移動至(965,545), 延遲0ms, T=0s000
>延遲100ms, T=0s000
>移動至(960,540), 延遲0ms, T=0s000

# 設定無限重複，間隔 4 分鐘（240秒）
# 在主程式設定：重複次數 = 0, 重複間隔 = 00:04:00`,
    tips: [
      '將重複次數設為 0（無限）',
      '將重複間隔設為 00:04:00',
      '確保滑鼠移動的位置不會誤觸其他程式'
    ]
  },
  {
    id: 'testing',
    category: '🧪 軟體測試',
    title: 'UI 自動化測試',
    description: '測試登入流程並驗證結果',
    code: `# UI 自動化測試 - 登入流程
#開始測試
>辨識>pic登入按鈕, T=0s000
>>#找到登入頁面
>>>#登入頁面未找到

#找到登入頁面
>左鍵點擊(500,300), 延遲50ms, T=0s000
>延遲200ms, T=0s000
>按test@example.com, 延遲0ms, T=0s000
>延遲300ms, T=0s000
>按Tab, 延遲50ms, T=0s000
>延遲200ms, T=0s000
>按test123456, 延遲0ms, T=0s000
>延遲300ms, T=0s000
>左鍵點擊>pic登入按鈕, T=0s000
>延遲2000ms, T=0s000
>>#驗證登入結果

#驗證登入結果
>辨識>pic歡迎畫面, T=0s000
>>#測試通過
>>>#測試失敗

#測試通過
>延遲500ms, T=0s000
# 測試通過

#測試失敗
>延遲500ms, T=0s000
# 測試失敗

#登入頁面未找到
>延遲500ms, T=0s000
# 找不到登入頁面`,
    tips: [
      '替換為實際的測試帳號密碼',
      '需要截取登入按鈕和歡迎畫面的圖片',
      '可擴展為更完整的測試流程'
    ]
  }
];

// 範例卡片元件
const ExampleCard = ({ 
  example,
  isExpanded,
  onToggle
}: { 
  example: typeof examples[0];
  isExpanded: boolean;
  onToggle: () => void;
}) => (
  <div className={`${styles.stepCard} ${isExpanded ? styles.expanded : ''}`}>
    <div className={styles.stepHeader} onClick={onToggle}>
      <div className={styles.stepNumber} style={{ fontSize: '1.5rem', width: 56, height: 56 }}>
        {example.category.split(' ')[0]}
      </div>
      <div className={styles.stepInfo}>
        <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>{example.category}</span>
        <h3>{example.title}</h3>
        <p>{example.description}</p>
      </div>
      <div className={styles.expandIcon}>{isExpanded ? '▲' : '▼'}</div>
    </div>
    {isExpanded && (
      <div className={styles.stepContent}>
        <h4>腳本內容</h4>
        <div className={styles.codeBlock}>
          <pre>{example.code}</pre>
        </div>

        <h4>使用提示</h4>
        <ul>
          {example.tips.map((tip, index) => (
            <li key={index}>{tip}</li>
          ))}
        </ul>

        <button
          className={styles.completeBtn}
          onClick={(e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(example.code);
            alert('腳本已複製到剪貼簿！');
          }}
        >
          📋 複製腳本
        </button>
      </div>
    )}
  </div>
);

export default function ExamplesPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1>📋 範例腳本</h1>
        <p>實用的自動化腳本範例，可直接複製使用</p>
      </div>

      <nav className={styles.nav}>
        <a href="/tutorial">← 返回教學首頁</a>
        <a href="/tutorial/basic">基礎教學</a>
        <a href="/tutorial/advanced">進階教學</a>
      </nav>

      <section className={styles.tutorialList}>
        {examples.map((example) => (
          <ExampleCard
            key={example.id}
            example={example}
            isExpanded={expandedId === example.id}
            onToggle={() => setExpandedId(expandedId === example.id ? null : example.id)}
          />
        ))}
      </section>

      <section className={styles.nextSteps}>
        <h2>🎯 進一步學習</h2>
        <div className={styles.nextGrid}>
          <a href="/tutorial/advanced" className={styles.nextCard}>
            <h3>進階功能</h3>
            <p>學習更多進階技巧</p>
          </a>
          <a href="https://github.com/Lucienwooo/ChroLens-Mimic/tree/main/main/scripts" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>更多範例</h3>
            <p>GitHub 上的完整範例</p>
          </a>
          <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>分享你的腳本</h3>
            <p>在社群分享你的創作</p>
          </a>
        </div>
      </section>
    </main>
  );
}
