import styles from '../page.module.css';

export default function ScriptEditor() {
    return (
        <div className={styles.page}>
            <h2>✏️ 腳本編輯器</h2>

            <h3>📋 指令分類總覽</h3>

            <h4>⌨️ 鍵盤操作</h4>
            <table>
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
                        <td>只按下不放開（用於組合鍵）</td>
                        <td><code>&gt;按下Ctrl, 延遲0ms, T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>放開[按鍵]</code></td>
                        <td>放開已按下的按鍵</td>
                        <td><code>&gt;放開Ctrl, 延遲0ms, T=0s100</code></td>
                    </tr>
                </tbody>
            </table>

            <p><strong>支援的按鍵：</strong>字母 A-Z、數字 0-9、功能鍵 F1-F12、特殊鍵（Enter, Space, Tab, Escape, Backspace）、修飾鍵（Ctrl, Shift, Alt, Win）、方向鍵（Up, Down, Left, Right）</p>

            <h4>🖱️ 滑鼠操作</h4>
            <table>
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
                        <td><code>中鍵點擊(X,Y)</code></td>
                        <td>在指定位置點擊中鍵</td>
                        <td><code>&gt;中鍵點擊(500,300), T=0s300</code></td>
                    </tr>
                    <tr>
                        <td><code>雙擊(X,Y)</code></td>
                        <td>快速點擊兩次</td>
                        <td><code>&gt;雙擊(500,300), T=0s400</code></td>
                    </tr>
                    <tr>
                        <td><code>按下left鍵(X,Y)</code></td>
                        <td>按住左鍵不放（拖曳起點）</td>
                        <td><code>&gt;按下left鍵(100,100), T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>放開left鍵(X,Y)</code></td>
                        <td>放開左鍵（拖曳終點）</td>
                        <td><code>&gt;放開left鍵(500,500), T=0s500</code></td>
                    </tr>
                </tbody>
            </table>

            <h4>🖼️ 圖片辨識操作</h4>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '25%' }}>指令</th>
                        <th style={{ width: '45%' }}>說明</th>
                        <th style={{ width: '30%' }}>範例</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>辨識&gt;pic##</code></td>
                        <td>找到圖片位置（不移動滑鼠）</td>
                        <td><code>&gt;辨識&gt;pic01, T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>移動至&gt;pic##</code></td>
                        <td>移動滑鼠到圖片中心</td>
                        <td><code>&gt;移動至&gt;pic01, T=0s100</code></td>
                    </tr>
                    <tr>
                        <td><code>左鍵點擊&gt;pic##</code></td>
                        <td>點擊圖片（點擊後滑鼠回到原位）</td>
                        <td><code>&gt;左鍵點擊&gt;pic01, T=0s200</code></td>
                    </tr>
                    <tr>
                        <td><code>右鍵點擊&gt;pic##</code></td>
                        <td>右鍵點擊圖片</td>
                        <td><code>&gt;右鍵點擊&gt;pic01, T=0s300</code></td>
                    </tr>
                    <tr>
                        <td><code>辨識任一&gt;pic##|pic##</code></td>
                        <td>同時找多張圖片（找到任何一張即可）</td>
                        <td><code>&gt;辨識任一&gt;pic01|pic02, T=0s000</code></td>
                    </tr>
                </tbody>
            </table>

            <p><strong>圖片命名規則：</strong>使用 pic 開頭的任意命名方式，例如：</p>
            <ul>
                <li>純數字編號：pic01, pic02, pic999</li>
                <li>中文描述：pic血量警告, pic怪物目標, pic確定按鈕</li>
                <li>中文+數字：pic王01, pic王02, pic小怪03</li>
                <li>英文描述：pic右上角, pic_button, pic_monster</li>
            </ul>
            <p>編輯器會自動搜尋資料夾內相同名稱的圖片檔（支援 .png, .jpg, .jpeg 等格式），無需寫完整副檔名</p>

            <h4>📝 OCR 文字辨識操作</h4>
            <p><strong>系統需求：</strong>Windows 10/11 內建 OCR 引擎（免安裝），或安裝 Tesseract OCR</p>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '25%' }}>指令</th>
                        <th style={{ width: '45%' }}>說明</th>
                        <th style={{ width: '30%' }}>範例</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>if文字&gt;[文字]</code></td>
                        <td>檢查螢幕上是否出現指定文字（最多等待10秒）</td>
                        <td><code>&gt;if文字&gt;確認, T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>等待文字&gt;[文字], 最長[秒數]s</code></td>
                        <td>等待特定文字出現在螢幕上，超時則繼續執行</td>
                        <td><code>&gt;等待文字&gt;載入完成, 最長15s, T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>點擊文字&gt;[文字]</code></td>
                        <td>找到螢幕上的文字並點擊該位置</td>
                        <td><code>&gt;點擊文字&gt;登入, T=0s000</code></td>
                    </tr>
                </tbody>
            </table>

            <p><strong>✨ OCR 特色：</strong></p>
            <ul>
                <li>🔍 <strong>智慧辨識</strong> - 自動偵測螢幕上的文字內容，無需截圖</li>
                <li>🚀 <strong>免安裝</strong> - Windows 10/11 內建 OCR 引擎，開箱即用</li>
                <li>🌐 <strong>多語言</strong> - 支援繁體中文、英文等多種語言</li>
                <li>⚡ <strong>容錯機制</strong> - OCR 引擎無法使用時，會自動跳過相關指令（不報錯）</li>
            </ul>

            <h4>⏱️ 延遲控制</h4>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '25%' }}>指令</th>
                        <th style={{ width: '45%' }}>說明</th>
                        <th style={{ width: '30%' }}>範例</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>延遲[毫秒數]ms</code></td>
                        <td>暫停執行指定時間（毫秒）</td>
                        <td><code>&gt;延遲500ms, T=0s000</code></td>
                    </tr>
                </tbody>
            </table>

            <p><strong>時間參數說明：</strong></p>
            <ul>
                <li><code>延遲時間</code> - 執行該動作後，等待多久才執行下一個動作（例如：延遲500ms）</li>
                <li><code>T=0s000</code> - 該動作在腳本中的絕對執行時間點（格式：秒s毫秒，例如：T=1s500 表示 1.5 秒時執行）</li>
            </ul>

            <h4>🔀 條件判斷與流程控制</h4>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '25%' }}>指令</th>
                        <th style={{ width: '45%' }}>說明</th>
                        <th style={{ width: '30%' }}>範例</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>if&gt;pic##</code></td>
                        <td>檢查圖片是否存在</td>
                        <td><code>&gt;if&gt;pic01, T=0s000</code></td>
                    </tr>
                    <tr>
                        <td><code>&gt;&gt;</code></td>
                        <td>成功分支（圖片存在時執行）</td>
                        <td><code>&gt;&gt;#找到了</code> 或 <code>&gt;&gt;</code>（留空=繼續）</td>
                    </tr>
                    <tr>
                        <td><code>&gt;&gt;&gt;</code></td>
                        <td>失敗分支（圖片不存在時執行）</td>
                        <td><code>&gt;&gt;&gt;#重試</code> 或 <code>&gt;&gt;&gt;</code>（留空=繼續）</td>
                    </tr>
                    <tr>
                        <td><code>#標籤名</code></td>
                        <td>定義標籤（跳轉目標）</td>
                        <td><code>#開始</code></td>
                    </tr>
                    <tr>
                        <td><code>#標籤名*N</code></td>
                        <td>定義帶有計數器的標籤（重複N次後自動繼續）</td>
                        <td><code>#刷怪*10</code></td>
                    </tr>
                    <tr>
                        <td><code>跳到#標籤名</code></td>
                        <td>跳轉到指定標籤</td>
                        <td><code>&gt;跳到#開始, T=1s000</code></td>
                    </tr>
                    <tr>
                        <td><code>停止</code></td>
                        <td>停止腳本執行</td>
                        <td><code>&gt;停止, T=2s000</code></td>
                    </tr>
                </tbody>
            </table>

            <p><strong>🔄 標籤計數器說明：</strong></p>
            <ul>
                <li>使用 <code>#標籤名*N</code> 格式可以設定標籤重複次數</li>
                <li>當跳轉到該標籤 N 次後，會自動忽略跳轉，繼續執行後續指令</li>
                <li>範例：<code>#刷怪*10</code> 表示重複刷怪 10 次後自動停止迴圈</li>
            </ul>

            <h3>📍 腳本編輯器功能說明</h3>
            <p>腳本編輯器可以讓您用文字格式編輯自動化腳本，相比純錄製更加靈活和強大。編輯器支援<strong>語法高亮</strong>功能，指令符號（<span className="syntax-operator">&gt;</span>、<span className="syntax-operator">&gt;&gt;</span>、<span className="syntax-operator">&gt;&gt;&gt;</span>、<span className="syntax-operator">,</span>、<span className="syntax-operator">T=</span>）會以<span className="syntax-operator">橘色</span>顯示，標籤（<span className="syntax-keyword">#標籤名</span>）會以<span className="syntax-keyword">青綠色</span>顯示，讓程式碼更易讀。</p>

            <h4>指令格式</h4>
            <pre><span className="syntax-operator">&gt;</span>動作內容<span className="syntax-operator">,</span> 延遲時間<span className="syntax-operator">,</span> <span className="syntax-operator">T=</span>執行時間點</pre>

            <h4>🖼️ 圖片辨識截圖</h4>
            <ol>
                <li>在腳本編輯器中點擊「📷 圖片辨識」按鈕</li>
                <li>編輯器會最小化，螢幕變暗並顯示十字游標</li>
                <li>按住滑鼠左鍵拖曳，選取要辨識的區域</li>
                <li>放開滑鼠後，圖片會自動儲存並命名（預設為 pic01, pic02...，您也可以自行重新命名為 pic血條、pic怪物 等有意義的名稱）</li>
                <li>編輯器恢復，可以使用該圖片編寫指令</li>
            </ol>

            <h4>💾 自訂模組</h4>
            <ul>
                <li><strong>儲存模組：</strong>反白選取常用的指令片段 → 右鍵 → 選擇「儲存為自訂模組」→ 輸入模組名稱</li>
                <li><strong>載入模組：</strong>在腳本編輯器中右鍵 → 選擇「插入自訂模組」→ 選擇要插入的模組</li>
                <li><strong>模組管理：</strong>模組儲存在 <code>scripts/modules/</code> 資料夾，可手動編輯或刪除</li>
            </ul>
        </div>
    );
}
