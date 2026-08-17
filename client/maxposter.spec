# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller untuk Maxposter (client).

CATATAN PENTING: CustomTkinter menyimpan file tema (.json) dan aset internal
di dalam folder paketnya sendiri. Jika file-file ini tidak diikutsertakan
secara eksplisit, aplikasi hasil build akan error saat dijalankan
("FileNotFoundError" mencari file tema). Baris `datas` di bawah ini
menyalin seluruh folder customtkinter apa adanya untuk menghindari itu.
"""
import customtkinter
from pathlib import Path

ctk_path = Path(customtkinter.__file__).parent

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(ctk_path), 'customtkinter'),
        ('maxposter_client/assets', 'maxposter_client/assets'),
    ],
    hiddenimports=['PIL._tkinter_finder'],
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
    name='Maxposter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='maxposter_client/assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Maxposter',
)
