import sqlite3
import os
import time

class GalleryDBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    folder TEXT NOT NULL,
                    rel_path TEXT NOT NULL UNIQUE,
                    modified_time REAL,
                    size INTEGER
                )
            ''')
            # Create indexes for faster searching
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_folder ON images(folder)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON images(name)')
            conn.commit()

    def sync_directory(self, images_root):
        """
        Synchronize the database with the physical directory.
        Adds new files, updates modified files, removes deleted files.
        """
        if not os.path.exists(images_root):
            return

        current_files = {}
        for root, dirs, files in os.walk(images_root):
            # Ignore hidden directories like .thumbnails
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, images_root).replace('\\', '/')
                    folder = os.path.relpath(root, images_root).replace('\\', '/')
                    if folder == '.':
                        folder = ''
                    try:
                        stat = os.stat(abs_path)
                        current_files[rel_path] = {
                            'name': f,
                            'folder': folder,
                            'modified_time': stat.st_mtime,
                            'size': stat.st_size
                        }
                    except Exception:
                        pass

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Fetch existing records
            cursor.execute('SELECT rel_path, modified_time, size FROM images')
            existing = {row[0]: {'modified_time': row[1], 'size': row[2]} for row in cursor.fetchall()}

            # Find deletions
            to_delete = [path for path in existing if path not in current_files]
            if to_delete:
                cursor.executemany('DELETE FROM images WHERE rel_path = ?', [(p,) for p in to_delete])

            # Find additions and modifications
            to_insert = []
            to_update = []
            for path, info in current_files.items():
                if path not in existing:
                    to_insert.append((info['name'], info['folder'], path, info['modified_time'], info['size']))
                else:
                    if existing[path]['modified_time'] != info['modified_time'] or existing[path]['size'] != info['size']:
                        to_update.append((info['name'], info['folder'], info['modified_time'], info['size'], path))

            if to_insert:
                cursor.executemany('''
                    INSERT INTO images (name, folder, rel_path, modified_time, size)
                    VALUES (?, ?, ?, ?, ?)
                ''', to_insert)

            if to_update:
                cursor.executemany('''
                    UPDATE images 
                    SET name = ?, folder = ?, modified_time = ?, size = ?
                    WHERE rel_path = ?
                ''', to_update)

            conn.commit()

    def get_folders(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT folder FROM images ORDER BY folder')
            return [row[0] for row in cursor.fetchall()]

    def search_images(self, folder=None, keyword=None):
        query = 'SELECT rel_path, name, folder FROM images WHERE 1=1'
        params = []
        if folder is not None:
            query += ' AND folder = ?'
            params.append(folder)
        if keyword:
            query += ' AND name LIKE ?'
            params.append(f'%{keyword}%')
        
        query += ' ORDER BY modified_time DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [{'rel_path': row[0], 'name': row[1], 'folder': row[2]} for row in cursor.fetchall()]

    def rename_image(self, old_rel_path, new_name, new_rel_path):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE images 
                SET name = ?, rel_path = ? 
                WHERE rel_path = ?
            ''', (new_name, new_rel_path, old_rel_path))
            conn.commit()

    def delete_image(self, rel_path):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM images WHERE rel_path = ?', (rel_path,))
            conn.commit()
