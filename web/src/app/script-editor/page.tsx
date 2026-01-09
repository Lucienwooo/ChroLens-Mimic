import styles from '../page.module.css';

export default function ScriptEditor() {
    return (
        <div className={styles.page}>
            <h1 style={{ textAlign: 'center', color: '#4CAF50' }}>✏️ ChroLens Mimic 腳本編輯器</h1>

            {/* 快速導航 */}
            <div style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                padding: '20px',
                borderRadius: '10px',
                marginBottom: '30px',
                color: 'white'
            }}>
                <h2 style={{ margin: '0 0 15px 0' }}>🚀 快速開始</h2>
                <ol style={{ margin: 0, paddingLeft: '20px' }}>
                    <li><strong>新手?</strong> 從「範例模板」開始,複製貼上即可使用</li>
                    <li><strong>想錄製?</strong> 點擊「錄製」按鈕,執行你的操作,自動生成腳本</li>
                    <li><strong>想手寫?</strong> 參考下方指令表,使用文字編輯器編寫腳本</li>
                    <li><strong>想視覺化?</strong> 勾選「圖形模式」,查看流程圖</li>
                </ol>
            </div>

            {/* 範例模板區 */}
            <div style={{
                background: '#f0f8ff',
                padding: '20px',
                borderRadius: '10px',
                marginBottom: '30px',
                border: '2px solid #4CAF50'
            }}>
                <h2>📦 範例模板庫</h2>
                <p>複製以下範例,快速開始你的自動化之旅!</p>

                <details style={{ marginBottom: '15px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold', padding: '10px', background: '#e8f5e9', borderRadius: '5px' }}>
                        🟢 入門: 自動點擊 (適合新手)
                    </summary>
                    <pre style={{ background: '#fff', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>{`# 每秒點擊螢幕中央
#開始
>左鍵點擊(960,540), 延遲100ms, T=0s000
>延遲1000ms, T=0s100
>跳轉#開始, T=1s100`}</pre>
                </details>

                <details style={{ marginBottom: '15px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold', padding: '10px', background: '#fff3e0', borderRadius: '5px' }}>
                        🟡 中級: 圖片辨識點擊
                    </summary>
                    <pre style={{ background: '#fff', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>{`# 找到按鈕並點擊
>if>pic開始按鈕, T=0s000
>>左鍵點擊, AI:pic開始按鈕, T=0s100
>>>延遲500ms, T=0s200`}</pre>
                </details>

                <details style={{ marginBottom: '15px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold', padding: '10px', background: '#ffebee', borderRadius: '5px' }}>
                        🔴 進階: 遊戲掛機 (含觸發器)
                    </summary>
                    <pre style={{ background: '#fff', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>{`# 主循環: 攻擊
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

                <p style={{ marginTop: '15px', fontStyle: 'italic', color: '#666' }}>
                    💡 提示: 更多範例請查看專案的 <code>templates/</code> 資料夾
                </p>
            </div>

            {/* 指令速查表 */}
            <h2>📋 指令速查表</h2>
            <p style={{ color: '#666', marginBottom: '20px' }}>
                點擊分類展開查看詳細指令。所有指令都遵循 <code>&gt;動作, 延遲, T=時間</code> 的格式。
            </p>

            <details open>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#2196F3' }}>
                    ⌨️ 鍵盤操作
                </summary>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#e3f2fd' }}>
                            <th style={{ width: '25%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '45%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>按[按鍵]</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>按下後立即放開</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;按Enter, 延遲50ms, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>按下[按鍵]</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>只按下不放開（組合鍵）</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;按下Ctrl, 延遲0ms, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>放開[按鍵]</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>放開已按下的按鍵</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;放開Ctrl, 延遲0ms, T=0s100</code></td>
                        </tr>
                    </tbody>
                </table>
                <p style={{ fontSize: '0.9em', color: '#666', marginTop: '-10px', marginBottom: '20px' }}>
                    <strong>支援按鍵:</strong> A-Z, 0-9, F1-F12, Enter, Space, Tab, Escape, Backspace, Ctrl, Shift, Alt, Win, 方向鍵
                </p>
            </details>

            <details>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#FF9800' }}>
                    🖱️ 滑鼠操作
                </summary>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#fff3e0' }}>
                            <th style={{ width: '25%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '45%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>移動至(X,Y)</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>移動滑鼠到指定座標</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;移動至(500,300), T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>左鍵點擊(X,Y)</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>在指定位置點擊左鍵</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;左鍵點擊(500,300), T=0s100</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>右鍵點擊(X,Y)</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>在指定位置點擊右鍵</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;右鍵點擊(500,300), T=0s200</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>雙擊(X,Y)</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>快速點擊兩次</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;雙擊(500,300), T=0s400</code></td>
                        </tr>
                    </tbody>
                </table>
            </details>

            <details>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#4CAF50' }}>
                    🖼️ 圖片辨識 (含 AI)
                </summary>
                <div style={{ background: '#e8f5e9', padding: '15px', borderRadius: '5px', marginBottom: '10px' }}>
                    <p style={{ margin: '0 0 10px 0' }}>
                        <strong>✨ 新功能:</strong> 支援 YOLO AI 物件偵測! 使用 <code>AI:標籤名</code> 啟用智能辨識
                    </p>
                    <p style={{ margin: 0, fontSize: '0.9em' }}>
                        傳統圖片辨識: <code>&gt;if&gt;pic按鈕</code><br />
                        AI 智能辨識: <code>&gt;if&gt;AI:button</code>
                    </p>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#e8f5e9' }}>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '40%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>辨識&gt;pic##</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>找到圖片位置（不移動）</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;辨識&gt;pic01, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>移動至&gt;pic##</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>移動滑鼠到圖片中心</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;移動至&gt;pic01, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>左鍵點擊&gt;pic##</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>找到圖片並點擊</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;左鍵點擊&gt;pic01, T=0s000</code></td>
                        </tr>
                        <tr style={{ background: '#fff9c4' }}>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>if&gt;AI:標籤</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><strong>✨ AI 條件判斷</strong></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;if&gt;AI:enemy, T=0s000</code></td>
                        </tr>
                        <tr style={{ background: '#fff9c4' }}>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>左鍵點擊&gt;AI:標籤</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><strong>✨ AI 智能點擊</strong></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;左鍵點擊&gt;AI:button, T=0s000</code></td>
                        </tr>
                    </tbody>
                </table>
            </details>

            <details>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#9C27B0' }}>
                    🔄 流程控制
                </summary>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#f3e5f5' }}>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '40%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>#標籤名</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>定義跳轉標籤</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>#主循環</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>跳轉#標籤</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>跳轉到指定標籤</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;跳轉#主循環, T=1s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>if&gt;圖片</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>條件判斷（找到/未找到）</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;if&gt;pic01, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;&gt;成功動作</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>條件成立時執行</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;&gt;跳轉#找到了</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;&gt;&gt;失敗動作</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>條件不成立時執行</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;&gt;&gt;跳轉#沒找到</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>重複&gt;N次</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>重複執行 N 次</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;重複&gt;10次, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>循環結束</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>結束循環區塊</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;循環結束, T=1s000</code></td>
                        </tr>
                    </tbody>
                </table>
            </details>

            <details>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#F44336' }}>
                    ⚡ 觸發器系統 (背景執行)
                </summary>
                <div style={{ background: '#ffebee', padding: '15px', borderRadius: '5px', marginBottom: '10px' }}>
                    <p style={{ margin: 0 }}>
                        <strong>🔥 強大功能:</strong> 觸發器可在背景持續監控,不影響主腳本執行!
                    </p>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#ffebee' }}>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '40%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>定時觸發&gt;間隔</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>每隔固定時間執行</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;定時觸發&gt;30秒</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>定時結束</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>結束定時觸發器</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;定時結束</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>條件觸發&gt;圖片</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>偵測到圖片時執行</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;條件觸發&gt;pic警告, 冷卻5000ms</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>條件結束</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>結束條件觸發器</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;條件結束</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>優先偵測&gt;圖片</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>偵測到時中斷主腳本</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;優先偵測&gt;pic血量低</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>優先偵測結束</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>結束優先觸發器</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;優先偵測結束</code></td>
                        </tr>
                    </tbody>
                </table>
                <pre style={{ background: '#fff', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>{`# 範例: 遊戲掛機腳本
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

            <details>
                <summary style={{ cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', marginBottom: '10px', color: '#607D8B' }}>
                    🎯 進階功能 (變數、狀態機)
                </summary>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                    <thead>
                        <tr style={{ background: '#eceff1' }}>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>指令</th>
                            <th style={{ width: '40%', padding: '10px', border: '1px solid #ddd' }}>說明</th>
                            <th style={{ width: '30%', padding: '10px', border: '1px solid #ddd' }}>範例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>設定變數&gt;名稱, 值</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>設定變數值</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;設定變數&gt;計數, 0, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>變數加1&gt;名稱</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>變數值 +1</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;變數加1&gt;計數, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>if變數&gt;名稱, 運算, 值</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>變數條件判斷</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;if變數&gt;計數, &gt;=, 10, T=0s000</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>狀態機&gt;名稱</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>開始狀態機定義</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;狀態機&gt;戰鬥AI</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>狀態&gt;名稱, 初始</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>定義初始狀態</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;狀態&gt;待機, 初始</code></td>
                        </tr>
                        <tr>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>切換&gt;條件&gt;狀態</code></td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>狀態切換規則</td>
                            <td style={{ padding: '8px', border: '1px solid #ddd' }}><code>&gt;切換&gt;success&gt;攻擊</code></td>
                        </tr>
                    </tbody>
                </table>
            </details>

            {/* 常見問題 */}
            <div style={{
                background: '#fff9c4',
                padding: '20px',
                borderRadius: '10px',
                marginTop: '30px'
            }}>
                <h2>❓ 常見問題</h2>

                <details style={{ marginBottom: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Q: 如何獲取滑鼠座標?</summary>
                    <p>A: 使用「錄製」功能,執行你的操作,系統會自動記錄座標。或使用 Windows 內建的「放大鏡」工具查看座標。</p>
                </details>

                <details style={{ marginBottom: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Q: 圖片辨識總是失敗?</summary>
                    <p>A: 1) 確認圖片大小適中(50-200px) 2) 使用「邊框」選項查看辨識位置 3) 降低信心度門檻 4) 嘗試使用 AI:標籤 啟用 YOLO 辨識</p>
                </details>

                <details style={{ marginBottom: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Q: 如何實現無限循環?</summary>
                    <p>A: 使用標籤和跳轉: <code>#開始</code> → 執行動作 → <code>&gt;跳轉#開始</code></p>
                </details>

                <details style={{ marginBottom: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Q: 觸發器和主腳本有什麼區別?</summary>
                    <p>A: 主腳本按順序執行,觸發器在背景持續監控。觸發器適合「定時任務」和「緊急處理」。</p>
                </details>

                <details>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Q: YOLO AI 辨識需要什麼?</summary>
                    <p>A: 需要安裝 ultralytics 套件,並準備訓練好的 YOLO 模型。使用 <code>AI:標籤名</code> 格式啟用。</p>
                </details>
            </div>

            {/* 底部提示 */}
            <div style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                padding: '20px',
                borderRadius: '10px',
                marginTop: '30px',
                color: 'white',
                textAlign: 'center'
            }}>
                <h3 style={{ margin: '0 0 10px 0' }}>🎉 開始你的自動化之旅!</h3>
                <p style={{ margin: 0 }}>
                    從範例模板開始 → 修改參數 → 測試執行 → 享受自動化帶來的便利
                </p>
            </div>
        </div>
    );
}
