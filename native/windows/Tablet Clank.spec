# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

root = Path(SPECPATH).parents[1]
revision = os.environ.get("TABLET_CLANK_PACKAGED_REVISION", "local development build")

a = Analysis(
    [str(root / "native" / "windows" / "launcher.py")],
    pathex=[str(root), str(root / "native" / "windows"), str(root / "native" / "macos")],
    binaries=[],
    datas=[],
    hiddenimports=["webapp", "dash_data", "dash_render", "dash_names", "tablet_clank.production", "tablet_clank.soak", "tablet_clank.sources.registry", "tablet_clank.storage.db"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Tablet Clank", console=False)
