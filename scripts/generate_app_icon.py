"""Generate the multi-resolution Windows icon from the canonical SVG asset."""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "robo_rec" / "gui" / "assets" / "app-icon.svg"
DESTINATION = SOURCE.with_suffix(".ico")
SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError(f"Could not encode the {size}px icon")
    return bytes(data)


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(SOURCE))
    if not renderer.isValid():
        raise RuntimeError(f"Could not load {SOURCE}")

    images = [(size, render_png(renderer, size)) for size in SIZES]
    header_size = 6 + 16 * len(images)
    offset = header_size
    entries = []
    payload = bytearray()

    for size, png in images:
        dimension = 0 if size == 256 else size
        entries.append(
            struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(png), offset)
        )
        payload.extend(png)
        offset += len(png)

    DESTINATION.write_bytes(
        struct.pack("<HHH", 0, 1, len(images)) + b"".join(entries) + payload
    )
    print(f"Generated {DESTINATION.relative_to(ROOT)}")
    app.quit()


if __name__ == "__main__":
    main()
