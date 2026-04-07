# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AST Index CLI tool.

Creates a standalone executable for Windows.
"""

block_cipher = None

a = Analysis(
    ['ast_index/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ast_index', 'ast_index'),
    ],
    hiddenimports=[
        'tree_sitter',
        'tree_sitter_python',
        'tree_sitter_c_sharp',
        'tree_sitter_javascript',
        'tree_sitter_typescript',
        'click',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ast-index',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
