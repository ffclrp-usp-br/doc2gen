# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['standalone/launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/templates', 'templates'),
        ('app/static', 'static'),
        ('app/media', 'media'),
    ],
    hiddenimports=[
        'django',
        'waitress',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='doc2gen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
