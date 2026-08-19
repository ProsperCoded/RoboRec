"""Icon loading — recolors bundled Lucide SVGs (assets/icons/) to theme colors.

Lucide icons ship with stroke="currentColor", which Qt's SVG renderer doesn't
resolve, so recoloring is done by substituting the hex color into the SVG
markup before handing it to QSvgRenderer, then caching the result as a QIcon.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICONS_DIR = Path(__file__).parent / "assets" / "icons"


@cache
def _colored_svg_bytes(name: str, color: str) -> bytes:
    raw = (ICONS_DIR / f"{name}.svg").read_text()
    return raw.replace("currentColor", color).encode("utf-8")


@cache
def load_icon(name: str, color: str, size: int = 20) -> QIcon:
    """Load a bundled SVG icon (assets/icons/<name>.svg) recolored to `color`."""
    renderer = QSvgRenderer(QByteArray(_colored_svg_bytes(name, color)))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


@cache
def load_pixmap(name: str, color: str, size: int = 20) -> QPixmap:
    """Same as load_icon but returns a QPixmap, for use in QLabel icons."""
    return load_icon(name, color, size).pixmap(size, size)
