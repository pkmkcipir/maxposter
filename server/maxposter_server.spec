# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller untuk Maxposter Server.

CATATAN PENTING: uvicorn memuat sebagian modulnya secara dinamis (auto-detect
event loop & protokol), begitu juga passlib (auto-detect backend hashing).
PyInstaller tidak bisa mendeteksi ini lewat analisis statis biasa, sehingga
harus didaftarkan manual di hiddenimports. Tanpa ini, .exe hasil build bisa
gagal start dengan error ModuleNotFoundError meski semua terlihat normal
saat dijalankan langsung lewat "python run_server.py".
"""

a = Analysis(
    ['run_server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'passlib.handlers.bcrypt',
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
    [],
    exclude_binaries=True,
    name='MaxposterServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MaxposterServer',
)
