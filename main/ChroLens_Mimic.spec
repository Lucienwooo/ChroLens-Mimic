# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('images', 'images'), ('TTF', 'TTF'), ('models', 'models'), ('data', 'data'), ('..\\umi_奶茶色.ico', '.')]
binaries = []
hiddenimports = ['ttkbootstrap', 'ttkbootstrap.constants', 'ttkbootstrap.themes', 'keyboard', 'mouse', 'mss', 'PIL', 'cv2', 'numpy', 'pystray', 'pynput', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'bezier_mouse', 'yolo_detector', 'recorder', 'text_script_editor', 'lang', 'script_io', 'about', 'mini', 'pynput_hotkey', 'window_selector', 'version_manager', 'version_info_dialog']
hiddenimports += collect_submodules('pynput')
tmp_ret = collect_all('ttkbootstrap')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ultralytics')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['ChroLens_Mimic.py'],
    pathex=['.', 'modules'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChroLens_Mimic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['..\\umi_奶茶色.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChroLens_Mimic',
)
