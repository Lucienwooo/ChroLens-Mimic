import styles from './page.module.css';

export default function Home() {
    return (
        <div className={styles.page}>
            <h2>📌 基本介紹</h2>

            <h3>🎯 ChroLens Mimic 是什麼？</h3>
            <p>ChroLens Mimic 是一款功能強大的 Windows 自動化工具，專為需要重複執行操作的使用者設計。透過精確的錄製與回放功能，結合圖片辨識和條件判斷，讓您輕鬆實現任何重複性工作的自動化。</p>

            <h3>✨ 核心特色</h3>
            <ul>
                <li><strong>🎯 精確錄製與回放</strong> - 記錄每一個鍵盤、滑鼠操作，並以可調速度精確重現</li>
                <li><strong>📝 腳本編輯器</strong> - 使用簡潔的文字指令語法，輕鬆編輯和管理自動化腳本</li>
                <li><strong>🖼️ 強化圖片辨識</strong> - 多算法融合、高精度匹配，支援多尺度搜尋</li>
                <li><strong>🔀 條件判斷與流程控制</strong> - if/else 分支、標籤跳轉、循環控制</li>
            </ul>

            <h3>🎮 適用場景</h3>
            <ul>
                <li><strong>遊戲自動化</strong> - 自動掛機、技能循環、任務重複</li>
                <li><strong>辦公自動化</strong> - 批次處理文件、表單填寫、數據錄入</li>
                <li><strong>測試與驗證</strong> - UI 自動化測試、重複性操作驗證</li>
            </ul>

            <h3>🎬 錄製與回放功能</h3>
            <p>錄製與回放是 ChroLens Mimic 的核心功能，可以精確記錄並重現您的鍵盤、滑鼠操作。類似於市面上的 <strong>按鍵精靈</strong>、<strong>MacroRecorder</strong>、<strong>Pulover's Macro Creator</strong> 等工具，但更專注於穩定性和圖片辨識功能。</p>

            <h4>⚡ 快捷鍵</h4>
            <ul>
                <li><code>F10</code> - 開始錄製</li>
                <li><code>F9</code> - 停止錄製</li>
                <li><code>F12</code> - 開始/暫停回放</li>
                <li><code>Esc</code> - 緊急停止</li>
            </ul>
        </div>
    );
}
