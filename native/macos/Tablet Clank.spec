# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

root = Path(SPECPATH).parents[1]
revision = os.environ.get("TABLET_CLANK_PACKAGED_REVISION", "local development build")

a = Analysis(
    [str(root / "native" / "macos" / "launcher.py")],
    pathex=[str(root), str(root / "native" / "macos")],
    binaries=[],
    datas=[],
    hiddenimports=["webapp", "tablet_clank.production", "tablet_clank.soak", "tablet_clank.sources.registry", "tablet_clank.storage.db"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Tablet Clank", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="Tablet Clank")
app = BUNDLE(coll, name="Tablet Clank.app", bundle_identifier="com.clank.tablet.fieldtest", info_plist={"CFBundleDisplayName": "Tablet Clank", "CFBundleShortVersionString": "0.1.0"})
