"""Resolve packaged resources independently of the current directory."""
from pathlib import Path
from PyQt5.QtGui import QIcon

ASSETS = Path(__file__).resolve().parent / "assets"


def asset_path(*parts):
    return str(ASSETS.joinpath(*parts))


def icon(name):
    return QIcon(asset_path("icons", name))
