# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 兼容 Windows 7 SP1 ~ Windows 11
将 VC++ Redist (ucrtbase + vcruntime140 + api-ms-win-crt-*) 打包进 EXE
DLL 解压到临时目录，Windows 加载器能正确找到所有依赖
"""
import os
import sys

# -----------------------------------------------------------
# 收集关键运行时 DLL（用于 Win7 兼容）
# -----------------------------------------------------------
redist_dir = os.path.join(os.getcwd(), 'redist')

redist_binaries = []
for f in os.listdir(redist_dir):
    fp = os.path.join(redist_dir, f)
    if os.path.isfile(fp) and f.lower().endswith('.dll'):
        # 放在临时目录根级别
        redist_binaries.append((fp, '.'))

# -----------------------------------------------------------
# 收集 Python 安装目录下所有 DLL
# -----------------------------------------------------------
python_dll_binaries = []
for dll_dir in [sys.prefix, os.path.join(sys.prefix, 'DLLs')]:
    if os.path.isdir(dll_dir):
        for f in os.listdir(dll_dir):
            if f.lower().endswith('.dll'):
                python_dll_binaries.append((os.path.join(dll_dir, f), '.'))

# 合并，vcruntime 优先用 redist 版本
all_binaries = redist_binaries + python_dll_binaries

# -----------------------------------------------------------
# 关键隐藏导入
# -----------------------------------------------------------
hiddenimports = [
    'winreg', 'ctypes', 'socket', 'subprocess', 'threading',
    'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.font',
    'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.constants',
    'tkinter.commondialog',
    '_tkinter',
    '_ctypes', '_ssl', '_socket',
    'queue', 'json', 'logging', 'traceback',
    'encodings.utf_8', 'encodings.gbk', 'encodings.ascii',
    'encodings.mbcs', 'encodings.aliases',
]

# -----------------------------------------------------------
# Analysis
# -----------------------------------------------------------
a = Analysis(
    ['PrinterShareFixer.py'],
    pathex=[],
    binaries=all_binaries,
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'unittest', 'pydoc',
        'distutils', 'setuptools', 'pip',
        'lib2to3', 'test', 'xmlrpc',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='打印机共享修复工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir='打印机共享修复_临时文件',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=None,
)
