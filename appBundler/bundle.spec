# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bundle.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('./mpy-cross/mpy-cross-win.exe', 'mpy-cross'),
        ('./mpy-cross/mpy-cross-mac-intel', 'mpy-cross'),
        ('./mpy-cross/mpy-cross-mac-arm', 'mpy-cross'),
        ('./mpy-cross/mpy-cross-linux-x86_64', 'mpy-cross'),
        ('./mpy-cross/mpy-cross-linux-arm', 'mpy-cross')
    ],
    hiddenimports=[],
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
    name='build_script',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='build_script.app',
    icon=None,
    bundle_identifier=None,
)
