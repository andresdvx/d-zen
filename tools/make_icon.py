"""Genera assets/icon.png y assets/icon.ico (multitamaño) con trazos vectoriales."""
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPen,
                           QPolygonF)

SIZES = (16, 24, 32, 48, 64, 128, 256)
OUT = Path(__file__).resolve().parents[1] / "assets"


def render(size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    s = float(size)
    g = QLinearGradient(0, 0, s, s)
    g.setColorAt(0, QColor("#8b5cf6"))
    g.setColorAt(1, QColor("#c026d3"))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(s * 0.03, s * 0.03, s * 0.94, s * 0.94), s * 0.24, s * 0.24)

    pen = QPen(QColor("white"), s * 0.085)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    pt = lambda x, y: QPointF(s * x, s * y)
    p.drawLine(pt(0.5, 0.22), pt(0.5, 0.58))                       # tallo
    p.drawPolyline(QPolygonF([pt(0.34, 0.44), pt(0.5, 0.60), pt(0.66, 0.44)]))  # punta
    p.drawPolyline(QPolygonF([pt(0.27, 0.66), pt(0.27, 0.77), pt(0.73, 0.77), pt(0.73, 0.66)]))  # bandeja
    p.end()
    return img


def png_bytes(img: QImage) -> bytes:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(ba)


def main() -> None:
    QGuiApplication(sys.argv)
    OUT.mkdir(exist_ok=True)
    render(256).save(str(OUT / "icon.png"))
    images = [png_bytes(render(n)) for n in SIZES]
    header = struct.pack("<HHH", 0, 1, len(SIZES))
    offset = 6 + 16 * len(SIZES)
    entries, blob = b"", b""
    for n, data in zip(SIZES, images):
        entries += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(data), offset + len(blob))
        blob += data
    (OUT / "icon.ico").write_bytes(header + entries + blob)
    print("OK", [len(i) for i in images])


if __name__ == "__main__":
    main()
