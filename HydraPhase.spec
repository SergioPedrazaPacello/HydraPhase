# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para HydraPhase.

Compilar localmente:
    pyinstaller HydraPhase.spec --noconfirm --clean

En GitHub Actions lo invoca .github/workflows/build.yml
"""
import os
from PyInstaller.utils.hooks import collect_data_files

# ── Recursos opcionales (icono, splash) ────────────────────────────────
datos = []
for f in ("hydraphase.ico", "splash.png"):
    if os.path.exists(f):
        datos.append((f, "."))

# matplotlib necesita sus fuentes y hojas de estilo empaquetadas
datos += collect_data_files("matplotlib", subdir="mpl-data")

ICONO = "hydraphase.ico" if os.path.exists("hydraphase.ico") else None

a = Analysis(
    ["app_hidra.py"],
    pathex=[],
    binaries=[],
    datas=datos,
    hiddenimports=[
        # Backend Qt de matplotlib (no lo detecta el analizador estatico)
        "matplotlib.backends.backend_qtagg",
        "matplotlib.backends.backend_agg",
        # Proyeccion 3D del esquema del pozo
        "mpl_toolkits.mplot3d",
        # Modulos propios cargados por nombre
        "engine_hidraulica",
        "estilo",
        "dialogos",
        "tab_datos",
        "tab_resultados",
        "tab_graficas",
        "tab_esquema",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Recorte de peso: backends y toolkits que no usamos
        "PyQt5", "PySide2", "PySide6",
        "tkinter", "PIL.ImageTk",
        "scipy", "pandas", "IPython", "jupyter",
        "matplotlib.backends.backend_tkagg",
        "matplotlib.backends.backend_webagg",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtMultimedia", "PyQt6.QtQml", "PyQt6.Qt3DCore",
        "PyQt6.QtBluetooth", "PyQt6.QtNetworkAuth", "PyQt6.QtPositioning",
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
    name="HydraPhase",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # --windowed : sin consola negra
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICONO,
)
