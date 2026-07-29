import json
import os

class PlaylistManager:
    """
    管理群組播放佇列的核心邏輯
    負責維護清單內容、存取、跳轉及次數遞減。
    """
    def __init__(self, app):
        self.app = app
        self.playlist_items = []  # List of dict: {'script': path, 'repeat': int, 'delay': int}
        self.current_index = 0
        self.is_playing = False
        self.autosave_file = os.path.join(self.app.app_dir, "autosaved_playlist.json")

    def get_items(self):
        return self.playlist_items

    def add_item(self, script_path, repeat=1, delay=0):
        self.playlist_items.append({
            'script': script_path,
            'repeat': repeat,
            'delay': delay
        })
        self.autosave()

    def remove_item(self, index):
        if 0 <= index < len(self.playlist_items):
            self.playlist_items.pop(index)
            self.autosave()

    def update_item(self, index, **kwargs):
        if 0 <= index < len(self.playlist_items):
            self.playlist_items[index].update(kwargs)
            self.autosave()

    def clear(self):
        self.playlist_items.clear()
        self.autosave()

    def autosave(self):
        try:
            with open(self.autosave_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlist_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Autosave playlist error: {e}")

    def load_autosaved(self):
        if os.path.exists(self.autosave_file):
            try:
                with open(self.autosave_file, 'r', encoding='utf-8') as f:
                    self.playlist_items = json.load(f)
            except Exception as e:
                print(f"Load autosaved playlist error: {e}")
                self.playlist_items = []
        return self.playlist_items
        
    def save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.playlist_items, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Save playlist error: {e}")
            return False

    def load_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.playlist_items = data
                    self.autosave()
                    return True
        except Exception as e:
            print(f"Load playlist error: {e}")
        return False
