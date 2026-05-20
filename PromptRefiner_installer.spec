# -*- mode: python ; coding: utf-8 -*-
# Installer build — cloud-only (Groq + Cerebras bundled keys, no local model download)
from PyInstaller.utils.hooks import collect_all

datas = [('prompts.json', '.'), ('_bundled_keys.py', '.')]
binaries = []
hiddenimports = ['pystray._win32', 'PIL._tkinter_finder']

for pkg in ['customtkinter', 'keyboard', 'pystray', 'pyperclip',
            'groq', 'cerebras', 'certifi', 'httpx']:
    tmp = collect_all(pkg)
    datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['llama_cpp', 'llama_cpp_python', 'huggingface_hub',
              'torch', 'transformers', 'numpy', 'scipy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PromptRefiner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='PromptRefiner',
)
