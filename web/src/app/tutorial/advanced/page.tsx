'use client';

import React, { useState } from 'react';
import styles from '../page.module.css';

// 程式碼區塊元件
const CodeBlock = ({ code, language = 'text' }: { code: string; language?: string }) => (
  <div className={styles.codeBlock}>
    <pre>{code}</pre>
  </div>
);

// 可展開區塊元件
const ExpandableSection = ({ 
  title, 
  children 
}: { 
  title: string;
  children: React.ReactNode;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={styles.stepCard}>
      <div 
        className={styles.stepHeader} 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={styles.stepInfo}>
          <h3>{title}</h3>
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
};

export default function AdvancedTutorialPage() {
  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1>🔧 進階功能教學</h1>
        <p>深入學習 ChroLens Mimic 的進階自動化功能</p>
      </div>

      <nav className={styles.nav}>
        <a href="/tutorial">← 返回教學首頁</a>
        <a href="/tutorial/basic">基礎教學</a>
        <a href="/tutorial/examples">範例腳本</a>
      </nav>

      <section className={styles.tutorialList}>
        <ExpandableSection title="🖼️ 圖片辨識功能">
          <h4>基本用法</h4>
          <p>圖片辨識讓你的腳本可以「看見」螢幕內容，根據畫面進行判斷。</p>
          
          <CodeBlock code={`# 基本辨識指令
>辨識>pic01, T=0s000

# 辨識成功後點擊
>左鍵點擊>pic01, T=0s000

# 帶範圍限制的辨識
>辨識>pic01, 範圍(100,200,500,600), T=0s000

# 顯示辨識邊框（用於調試）
>辨識>pic01, 邊框, T=0s000

# 組合使用
>辨識>pic血條, 邊框, 範圍(50,50,200,120), T=0s000`} />

          <h4>圖片命名規則</h4>
          <ul>
            <li>必須以 <code>pic</code> 開頭</li>
            <li>支援中文、英文、數字組合：<code>pic01</code>、<code>pic血條</code>、<code>pic確定按鈕</code></li>
            <li>圖片自動儲存到 <code>scripts/images/</code> 資料夾</li>
          </ul>

          <h4>截圖工具</h4>
          <p>在編輯器中點擊「截圖辨識」按鈕，即可截取螢幕區域並自動插入指令。</p>

          <div className={styles.tipBox}>
            <strong>💡 技巧：</strong>使用「範圍」參數可以限制搜尋區域，提高辨識速度和準確性。
          </div>
        </ExpandableSection>

        <ExpandableSection title="📝 OCR 文字辨識">
          <h4>文字辨識指令</h4>
          <p>使用 OCR 功能，你的腳本可以辨識和點擊螢幕上的文字。</p>
          
          <CodeBlock code={`# 判斷文字是否存在
>if文字>確定, T=0s000
>>#點擊確定
>>>#文字不存在

# 等待文字出現
>等待文字>載入完成, 最長10s, T=0s000

# 直接點擊文字
>點擊文字>開始遊戲, T=0s000`} />

          <h4>使用場景</h4>
          <ul>
            <li>點擊動態生成的按鈕（文字位置不固定）</li>
            <li>等待載入完成的提示</li>
            <li>自動選擇選單選項</li>
          </ul>

          <div className={styles.warningBox}>
            <strong>⚠️ 注意：</strong>OCR 辨識需要較多計算資源，過於頻繁使用可能影響效能。
          </div>
        </ExpandableSection>

        <ExpandableSection title="🔀 條件判斷與分支">
          <h4>if 條件判斷</h4>
          <p>使用條件判斷讓腳本根據情況執行不同的操作。</p>
          
          <CodeBlock code={`# 基本結構
#檢查目標
>辨識>pic敵人, T=0s000
>>#發現敵人    ← 辨識成功時跳轉
>>>#未發現敵人  ← 辨識失敗時跳轉

#發現敵人
>左鍵點擊>pic敵人, T=0s000
>>#攻擊

#未發現敵人
>延遲2000ms, T=0s000
>>#檢查目標    ← 繼續循環檢查`} />

          <h4>分支跳轉符號</h4>
          <table className={styles.hotkeyTable}>
            <thead>
              <tr>
                <th>符號</th>
                <th>意義</th>
                <th>使用時機</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>{'>>#標籤'}</code></td>
                <td>成功跳轉</td>
                <td>條件成立時</td>
              </tr>
              <tr>
                <td><code>{'>>>#標籤'}</code></td>
                <td>失敗跳轉</td>
                <td>條件不成立時</td>
              </tr>
            </tbody>
          </table>
        </ExpandableSection>

        <ExpandableSection title="📊 變數與計數器">
          <h4>變數操作</h4>
          <p>使用變數追蹤狀態和計數。</p>
          
          <CodeBlock code={`# 設定變數
>設定變數>攻擊次數, 0, T=0s000
>設定變數>最大次數, 10, T=0s000

# 變數加減
>變數加1>攻擊次數, T=0s000
>變數減1>剩餘次數, T=0s000

# 變數條件判斷
>if變數>攻擊次數, >=, 最大次數, T=0s000
>>#達到上限
>>>#繼續攻擊`} />

          <h4>計數器與計時器</h4>
          <CodeBlock code={`# 計數器：達到次數後觸發
>計數器>失敗次數, 3次後, T=0s000
>>#處理失敗
>重置計數器>失敗次數, T=0s000

# 計時器：超時後觸發
>計時器>搜尋怪物, 30秒後, T=0s000
>>#搜尋超時
>重置計時器>搜尋怪物, T=0s000`} />

          <div className={styles.tipBox}>
            <strong>💡 技巧：</strong>計數器和計時器非常適合處理「卡住」的情況，例如持續嘗試失敗時的錯誤處理。
          </div>
        </ExpandableSection>

        <ExpandableSection title="🔄 重複執行">
          <h4>重複區塊</h4>
          <p>使用重複指令執行固定次數的操作。</p>
          
          <CodeBlock code={`# 重複 5 次撿取動作
>重複>5次, T=0s000
>按z, 延遲50ms, T=0s000
>延遲200ms, T=0s000
>重複結束, T=0s000`} />

          <h4>隨機延遲</h4>
          <p>使用隨機延遲讓操作看起來更自然，避免被偵測為機器人。</p>
          
          <CodeBlock code={`# 隨機延遲 100-500ms
>隨機延遲>100ms,500ms, T=0s000

# 隨機執行（50% 機率執行）
>隨機執行>50%, T=0s000
>>#執行這個動作
>>>#跳過`} />
        </ExpandableSection>

        <ExpandableSection title="📦 自訂模組">
          <h4>建立模組</h4>
          <p>將常用的指令組合封裝成模組，方便重複使用。</p>
          
          <ol>
            <li>在編輯器中選取要封裝的指令</li>
            <li>右鍵選擇「儲存為自訂模組」</li>
            <li>輸入模組名稱（例如：<code>攻擊連招</code>）</li>
          </ol>

          <h4>使用模組</h4>
          <CodeBlock code={`# 引用自訂模組
>#mod_攻擊連招

# 模組檔案儲存位置
scripts/modules/mod_攻擊連招.txt`} />

          <div className={styles.tipBox}>
            <strong>💡 技巧：</strong>模組可以包含標籤和分支，像函式一樣組織複雜邏輯。
          </div>
        </ExpandableSection>
      </section>

      <section className={styles.nextSteps}>
        <h2>📚 相關資源</h2>
        <div className={styles.nextGrid}>
          <a href="/tutorial/examples" className={styles.nextCard}>
            <h3>範例腳本</h3>
            <p>實際應用案例</p>
          </a>
          <a href="https://github.com/Lucienwooo/ChroLens-Mimic" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>GitHub 原始碼</h3>
            <p>查看完整原始碼</p>
          </a>
          <a href="https://discord.gg/72Kbs4WPPn" target="_blank" rel="noopener noreferrer" className={styles.nextCard}>
            <h3>Discord 社群</h3>
            <p>提問與交流</p>
          </a>
        </div>
      </section>
    </main>
  );
}
