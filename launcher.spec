# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('django') +
    collect_submodules('compras') +
    collect_submodules('myproject')
)

a = Analysis(
    ['launcher.py'],

    pathex=[
        '.',
        './app',
    ],

    binaries=[],

  
    datas=[
        ('app/compras/templates', 'compras/templates'),
        ('app/static', 'static'),
        ('app/media', 'media'),
    ],

    hiddenimports=hiddenimports,

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
    [],
    exclude_binaries=True,
    name='launcher',
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='launcher',
)
