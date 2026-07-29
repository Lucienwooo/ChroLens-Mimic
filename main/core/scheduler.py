import threading
import time
import datetime

class ScheduleManager:
    """
    排程管理器 - 背景持續檢查時間並觸發排程腳本
    
    功能：
    - 主程式開著時自動檢查時間
    - 到達排程時間自動執行對應腳本
    - 衝突處理：若有腳本執行中，停止舊的、執行新的
    """
    
    def __init__(self, app):
        self.app = app
        self.schedules = {}  # {schedule_id: config}
        self.running = True
        self.last_trigger = {}  # 避免同一分鐘重複觸發 {schedule_id: "HH:MM"}
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        print("[OK] 排程管理器已啟動")
        # Note: Thread is started by ChroLens_Mimic.py originally? Let's check.
    
    def add_schedule(self, schedule_id, config):
        """
        新增排程
        """
        self.schedules[schedule_id] = config
        print(f"[OK] 已新增排程: {schedule_id} @ {config.get('time', '')}")
    
    def remove_schedule(self, schedule_id):
        """移除排程"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            print(f"[OK] 已移除排程: {schedule_id}")
    
    def _check_loop(self):
        """背景執行緒 - 每 5 秒檢查一次排程時間（確保準時觸發）"""
        while self.running:
            try:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%Y-%m-%d")
                
                for sid, config in list(self.schedules.items()):
                    if not config.get('enabled', True):
                        continue
                    
                    # 取得排程時間 (只取 HH:MM)
                    schedule_time = config.get('time', '')
                    if ':' in schedule_time:
                        schedule_time = schedule_time[:5]  # "15:30:00" -> "15:30"
                    
                    if schedule_time == current_time:
                        # 使用日期+時間作為 key，避免同一分鐘重複觸發
                        trigger_key = f"{current_date}_{current_time}"
                        if self.last_trigger.get(sid) == trigger_key:
                            continue
                        self.last_trigger[sid] = trigger_key
                        
                        # 在主執行緒觸發腳本
                        script_file = config.get('script')
                        callback = config.get('callback')
                        
                        if callback and script_file:
                            self.app.after(0, lambda s=script_file, c=callback: self._trigger_script(s, c))
                        
            except Exception as e:
                print(f"排程檢查錯誤: {e}")
            
            time.sleep(5)  # 每 5 秒檢查一次（確保最多延遲 5 秒）
    
    def _trigger_script(self, script_file, callback):
        """觸發排程腳本 - 若有衝突則停止舊的"""
        try:
            # 檢查是否有腳本正在執行
            if hasattr(self.app, 'playing') and self.app.playing:
                print(f"[WARN] 偵測到衝突：停止目前執行中的腳本")
                self.app.log(f"[WARN] 排程衝突：停止目前腳本，執行新排程")
                self.app.stop_all()
                time.sleep(0.5)  # 等待停止完成
            
            # 執行排程腳本
            print(f"[CLOCK] 觸發排程: {script_file}")
            self.app.log(f"[CLOCK] 排程觸發: {script_file}")
            callback(script_file)
            
        except Exception as e:
            print(f"觸發排程失敗: {e}")
            if hasattr(self.app, 'log'):
                self.app.log(f" 觸發排程失敗: {e}")
