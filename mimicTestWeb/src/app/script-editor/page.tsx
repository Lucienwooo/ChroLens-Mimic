'use client';

import React from 'react';
import styles from './page.module.css';

export default function ScriptEditor() {
    return (
        <div className={styles.container}>
            <h1 className={styles.title}>✏️ ChroLens Mimic 腳本編輯器</h1>

            {/* 快速導航 */}
            <div className={styles.banner}>
                <h2>🚀 快速開始</h2>
                <ol>
                    <li><strong>新手?</strong> 從「範例模板」開始,複製貼上即可使用</li>
                    <li><strong>想錄製?</strong> 點擊「錄製」按鈕,執行你的操作,自動生成腳本</li>
                    <li><strong>想手寫?</strong> 參考下方指令表,使用文字編輯器編寫腳本</li>
                    <li><strong>想視覺化?</strong> 勾選「圖形模式」,查看流程圖</li>
                </ol>
            </div>

            {/* 範例模板區 */}
            <div className={styles.section}>
                <h2 className={styles.sectionTitle}>📦 範例模板庫</h2>
                <p>複製以下範例,快速開始你的自動化之旅!</p>

                <details className={styles.details} style={{ marginTop: '1.5rem' }}>
                    <summary className={styles.summary}>
                        🟢 入門: 自動點擊 (適合新手)
                    </summary>
                    <pre className={styles.codeBlock}>{`# 每秒點擊螢幕中央
#開始
>左鍵點擊(960,540), 延遲100ms, T=0s000
>延遲1000ms, T=0s100
>跳轉#開始, T=1s100`}</pre>
                </details>

                <details className={styles.details}>
                    <summary className={styles.summary}>
                        🟡 中級: 圖片辨識點擊
                    </summary>
                    <pre className={styles.codeBlock}>{`# 找到按鈕並點擊
>if>pic開始按鈕, T=0s000
>>左鍵點擊, AI:pic開始按鈕, T=0s100
>>>延遲500ms, T=0s200`}</pre>
                </details>

                <details className={styles.details}>
                    <summary className={styles.summary}>
                        🔴 進階: 遊戲掛機 (含觸發器)
                    </summary>
                    <pre className={styles.codeBlock}>{`# 主循環: 攻擊
#主循環
>按1, 延遲50ms, T=0s000
>延遲800ms, T=0s050
>跳轉#主循環, T=0s850

# 背景: 每5秒撿道具
>定時觸發>5秒
>按F, 延遲50ms
>定時結束

# 緊急: 血量低自動補血
>優先偵測>pic血量低
>按2, 延遲50ms
>優先偵測結束`}</pre>
                </details>

                <div className={styles.tipBox}>
                    💡 提示: 更多範例請查看專案的 <code>templates/</code> 資料夾
                </div>
            </div>

            {/* 指令速查表 */}
            <h2 className={styles.sectionTitle} style={{ marginTop: '4rem' }}>📋 指令速查表</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                點擊分類展開查看詳細指令。所有指令都遵循 <code>&gt;動作, 延遲, T=時間</code> 的格式。
            </p>

            <details className={styles.details} open>
                <summary className={styles.summary} style={{ color: 'var(--primary)' }}>
                    ⌨️ 鍵盤操作
                </summary>
                <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '25%' }}>指令</th>
                                <th style={{ width: '45%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>按[按鍵]</code></td>
                                <td>按下後立即放開</td>
                                <td><code>&gt;按Enter, 延遲50ms, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>按下[按鍵]</code></td>
                                <td>只按下不放開（組合鍵）</td>
                                <td><code>&gt;按下Ctrl, 延遲0ms, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>放開[按鍵]</code></td>
                                <td>放開已按下的按鍵</td>
                                <td><code>&gt;放開Ctrl, 延遲0ms, T=0s100</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '0 1rem', marginBottom: '2rem' }}>
                    <strong>支援按鍵:</strong> A-Z, 0-9, F1-F12, Enter, Space, Tab, Escape, Backspace, Ctrl, Shift, Alt, Win, 方向鍵
                </p>
            </details>

            <details className={styles.details}>
                <summary className={styles.summary} style={{ color: '#FF9800' }}>
                    🖱️ 滑鼠操作
                </summary>
                <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '25%' }}>指令</th>
                                <th style={{ width: '45%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>移動至(X,Y)</code></td>
                                <td>移動滑鼠到指定座標</td>
                                <td><code>&gt;移動至(500,300), T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>左鍵點擊(X,Y)</code></td>
                                <td>在指定位置點擊左鍵</td>
                                <td><code>&gt;左鍵點擊(500,300), T=0s100</code></td>
                            </tr>
                            <tr>
                                <td><code>右鍵點擊(X,Y)</code></td>
                                <td>在指定位置點擊右鍵</td>
                                <td><code>&gt;右鍵點擊(500,300), T=0s200</code></td>
                            </tr>
                            <tr>
                                <td><code>雙擊(X,Y)</code></td>
                                <td>快速點擊兩次</td>
                                <td><code>&gt;雙擊(500,300), T=0s400</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </details>

            <details className={styles.details}>
                <summary className={styles.summary} style={{ color: 'var(--primary)' }}>
                    🖼️ 圖片辨識 (含 AI)
                </summary>
                <div style={{ padding: '1rem', background: 'rgba(0, 240, 255, 0.05)', borderBottom: '1px solid var(--border-color)' }}>
                    <p style={{ margin: '0 0 0.5rem 0' }}>
                        <strong>✨ 新功能:</strong> 支援 YOLO AI 物件偵測! 使用 <code>AI:標籤名</code> 啟用智能辨識
                    </p>
                    <p style={{ margin: 0, fontSize: '0.9em', color: 'var(--text-muted)' }}>
                        傳統圖片辨識: <code>&gt;if&gt;pic按鈕</code> | AI 智能辨識: <code>&gt;if&gt;AI:button</code>
                    </p>
                </div>
                <div className={styles.tableWrapper} style={{ borderTop: 'none', borderRadius: '0 0 8px 8px' }}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '30%' }}>指令</th>
                                <th style={{ width: '40%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>辨識&gt;pic##</code></td>
                                <td>找到圖片位置（不移動）</td>
                                <td><code>&gt;辨識&gt;pic01, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>移動至&gt;pic##</code></td>
                                <td>移動滑鼠到圖片中心</td>
                                <td><code>&gt;移動至&gt;pic01, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>左鍵點擊&gt;pic##</code></td>
                                <td>找到圖片並點擊</td>
                                <td><code>&gt;左鍵點擊&gt;pic01, T=0s000</code></td>
                            </tr>
                            <tr style={{ background: 'rgba(255, 235, 59, 0.05)' }}>
                                <td><code>if&gt;AI:標籤</code></td>
                                <td><strong>✨ AI 條件判斷</strong></td>
                                <td><code>&gt;if&gt;AI:enemy, T=0s000</code></td>
                            </tr>
                            <tr style={{ background: 'rgba(255, 235, 59, 0.05)' }}>
                                <td><code>左鍵點擊&gt;AI:標籤</code></td>
                                <td><strong>✨ AI 智能點擊</strong></td>
                                <td><code>&gt;左鍵點擊&gt;AI:button, T=0s000</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </details>

            <details className={styles.details}>
                <summary className={styles.summary} style={{ color: 'var(--accent)' }}>
                    🔄 流程控制
                </summary>
                <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '30%' }}>指令</th>
                                <th style={{ width: '40%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>#標籤名</code></td>
                                <td>定義跳轉標籤</td>
                                <td><code>#主循環</code></td>
                            </tr>
                            <tr>
                                <td><code>跳轉#標籤</code></td>
                                <td>跳轉到指定標籤</td>
                                <td><code>&gt;跳轉#主循環, T=1s000</code></td>
                            </tr>
                            <tr>
                                <td><code>if&gt;圖片</code></td>
                                <td>條件判斷（找到/未找到）</td>
                                <td><code>&gt;if&gt;pic01, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>&gt;&gt;成功動作</code></td>
                                <td>條件成立時執行</td>
                                <td><code>&gt;&gt;跳轉#找到了</code></td>
                            </tr>
                            <tr>
                                <td>&gt;&gt;&gt;失敗動作</td>
                                <td>條件不成立時執行</td>
                                <td><code>&gt;&gt;&gt;跳轉#沒找到</code></td>
                            </tr>
                            <tr>
                                <td><code>重複&gt;N次</code></td>
                                <td>重複執行 N 次</td>
                                <td><code>&gt;重複&gt;10次, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>循環結束</code></td>
                                <td>結束循環區塊</td>
                                <td><code>&gt;循環結束, T=1s000</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </details>

            <details className={styles.details}>
                <summary className={styles.summary} style={{ color: '#F44336' }}>
                    ⚡ 觸發器系統 (背景執行)
                </summary>
                <div style={{ padding: '1rem', background: 'rgba(244, 67, 54, 0.05)', borderBottom: '1px solid var(--border-color)' }}>
                    <p style={{ margin: 0 }}>
                        <strong>🔥 強大功能:</strong> 觸發器可在背景持續監控,不影響主腳本執行!
                    </p>
                </div>
                <div className={styles.tableWrapper} style={{ borderTop: 'none', borderRadius: '0 0 8px 8px' }}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '30%' }}>指令</th>
                                <th style={{ width: '40%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>定時觸發&gt;間隔</code></td>
                                <td>每隔固定時間執行</td>
                                <td><code>&gt;定時觸發&gt;30秒</code></td>
                            </tr>
                            <tr>
                                <td><code>定時結束</code></td>
                                <td>結束定時觸發器</td>
                                <td><code>&gt;定時結束</code></td>
                            </tr>
                            <tr>
                                <td><code>條件觸發&gt;圖片</code></td>
                                <td>偵測到圖片時執行</td>
                                <td><code>&gt;條件觸發&gt;pic警告, 冷卻5000ms</code></td>
                            </tr>
                            <tr>
                                <td><code>條件結束</code></td>
                                <td>結束條件觸發器</td>
                                <td><code>&gt;條件結束</code></td>
                            </tr>
                            <tr>
                                <td><code>優先偵測&gt;圖片</code></td>
                                <td>偵測到時中斷主腳本</td>
                                <td><code>&gt;優先偵測&gt;pic血量低</code></td>
                            </tr>
                            <tr>
                                <td><code>優先偵測結束</code></td>
                                <td>結束優先觸發器</td>
                                <td><code>&gt;優先偵測結束</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <pre className={styles.codeBlock}>{`# 範例: 遊戲掛機腳本
#主循環
>按1, 延遲50ms, T=0s000
>延遲800ms, T=0s050
>跳轉#主循環, T=0s850

# 背景: 每5秒撿道具
>定時觸發>5秒
>按F, 延遲50ms
>定時結束

# 緊急: 血量低立即補血
>優先偵測>pic血量低
>按2, 延遲50ms
>優先偵測結束`}</pre>
            </details>

            <details className={styles.details}>
                <summary className={styles.summary} style={{ color: '#607D8B' }}>
                    🎯 進階功能 (變數、狀態機)
                </summary>
                <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th style={{ width: '30%' }}>指令</th>
                                <th style={{ width: '40%' }}>說明</th>
                                <th style={{ width: '30%' }}>範例</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>設定變數&gt;名稱, 值</code></td>
                                <td>設定變數值</td>
                                <td><code>&gt;設定變數&gt;計數, 0, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>變數加1&gt;名稱</code></td>
                                <td>變數值 +1</td>
                                <td><code>&gt;變數加1&gt;計數, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>if變數&gt;名稱, 運算, 值</code></td>
                                <td>變數條件判斷</td>
                                <td><code>&gt;if變數&gt;計數, &gt;=, 10, T=0s000</code></td>
                            </tr>
                            <tr>
                                <td><code>狀態機&gt;名稱</code></td>
                                <td>開始狀態機定義</td>
                                <td><code>&gt;狀態機&gt;戰鬥AI</code></td>
                            </tr>
                            <tr>
                                <td><code>狀態&gt;名稱, 初始</code></td>
                                <td>定義初始狀態</td>
                                <td><code>&gt;狀態&gt;待機, 初始</code></td>
                            </tr>
                            <tr>
                                <td><code>切換&gt;條件&gt;狀態</code></td>
                                <td>狀態切換規則</td>
                                <td><code>&gt;切換&gt;success&gt;攻擊</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </details>

            {/* 常見問題 */}
            <div className={styles.faq}>
                <h2>❓ 常見問題</h2>

                <details>
                    <summary>Q: 如何獲取滑鼠座標?</summary>
                    <p>A: 使用「錄製」功能,執行你的操作,系統會自動記錄座標。或使用 Windows 內建的「放大鏡」工具查看座標。</p>
                </details>

                <details>
                    <summary>Q: 圖片辨識總是失敗?</summary>
                    <p>A: 1) 確認圖片大小適中(50-200px) 2) 使用「邊框」選項查看辨識位置 3) 降低信心度門檻 4) 嘗試使用 AI:標籤 啟用 YOLO 辨識</p>
                </details>

                <details>
                    <summary>Q: 如何實現無限循環?</summary>
                    <p>A: 使用標籤和跳轉: <code>#開始</code> → 執行動作 → <code>&gt;跳轉#開始</code></p>
                </details>

                <details>
                    <summary>Q: 觸發器和主腳本有什麼區別?</summary>
                    <p>A: 主腳本按順序執行,觸發器在背景持續監控。觸發器適合「定時任務」和「緊急處理」。</p>
                </details>

                <details>
                    <summary>Q: YOLO AI 辨識需要什麼?</summary>
                    <p>A: 需要安裝 ultralytics 套件,並準備訓練好的 YOLO 模型。使用 <code>AI:標籤名</code> 格式啟用。</p>
                </details>
            </div>

            {/* 底部提示 */}
            <div className={styles.footerBanner}>
                <h3>🎉 開始你的自動化之旅!</h3>
                <p style={{ margin: 0, color: 'var(--text-muted)' }}>
                    從範例模板開始 → 修改參數 → 測試執行 → 享受自動化帶來的便利
                </p>
            </div>
        </div>
    );
}
