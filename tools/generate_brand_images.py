#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import math
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "custom_components" / "hargassner_hv20" / "brand"

Color = tuple[int, int, int, int]
TRANSPARENT: Color = (0, 0, 0, 0)
YELLOW: Color = (255, 199, 44, 255)
RED: Color = (196, 18, 48, 255)
DARK: Color = (43, 43, 43, 255)
WHITE: Color = (255, 255, 255, 255)
SHADOW: Color = (0, 0, 0, 55)

FONT: dict[str, list[str]] = {
    "0": ["111", "101", "101", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["111", "001", "001", "111", "100", "100", "111"],
    "3": ["111", "001", "001", "111", "001", "001", "111"],
    "4": ["101", "101", "101", "111", "001", "001", "001"],
    "5": ["111", "100", "100", "111", "001", "001", "111"],
    "6": ["111", "100", "100", "111", "101", "101", "111"],
    "7": ["111", "001", "001", "010", "010", "010", "010"],
    "8": ["111", "101", "101", "111", "101", "101", "111"],
    "9": ["111", "101", "101", "111", "001", "001", "111"],
    "A": ["010", "101", "101", "111", "101", "101", "101"],
    "E": ["111", "100", "100", "111", "100", "100", "111"],
    "H": ["101", "101", "101", "111", "101", "101", "101"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["1001", "1101", "1011", "1001", "1001", "1001", "1001"],
    "O": ["111", "101", "101", "101", "101", "101", "111"],
    "S": ["111", "100", "100", "111", "001", "001", "111"],
    "T": ["111", "010", "010", "010", "010", "010", "010"],
    "V": ["101", "101", "101", "101", "101", "101", "010"],
    " ": ["0", "0", "0", "0", "0", "0", "0"],
    "-": ["0", "0", "0", "111", "0", "0", "0"],
}


def blend(dst: Color, src: Color) -> Color:
    sr, sg, sb, sa = src
    if sa == 255:
        return src
    if sa == 0:
        return dst
    dr, dg, db, da = dst
    a = sa / 255
    inv = 1 - a
    return (
        round(sr * a + dr * inv),
        round(sg * a + dg * inv),
        round(sb * a + db * inv),
        round(255 * (a + da / 255 * inv)),
    )


class Canvas:
    def __init__(self, width: int, height: int, bg: Color = TRANSPARENT) -> None:
        self.width = width
        self.height = height
        self.pixels = [bg] * (width * height)

    def set(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            self.pixels[idx] = blend(self.pixels[idx], color)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        for y in range(max(0, y0), min(self.height, y1)):
            for x in range(max(0, x0), min(self.width, x1)):
                self.set(x, y, color)

    def circle(self, cx: int, cy: int, r: int, color: Color) -> None:
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                    self.set(x, y, color)

    def rounded_rect(self, x0: int, y0: int, x1: int, y1: int, radius: int, color: Color) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                dx = max(x0 + radius - x, 0, x - (x1 - radius - 1))
                dy = max(y0 + radius - y, 0, y - (y1 - radius - 1))
                if dx * dx + dy * dy <= radius * radius:
                    self.set(x, y, color)

    def polygon(self, points: list[tuple[int, int]], color: Color) -> None:
        min_y = max(0, min(y for _, y in points))
        max_y = min(self.height - 1, max(y for _, y in points))
        for y in range(min_y, max_y + 1):
            nodes: list[int] = []
            j = len(points) - 1
            for i, (xi, yi) in enumerate(points):
                xj, yj = points[j]
                if (yi < y <= yj) or (yj < y <= yi):
                    nodes.append(int(xi + (y - yi) / (yj - yi) * (xj - xi)))
                j = i
            nodes.sort()
            for i in range(0, len(nodes), 2):
                if i + 1 >= len(nodes):
                    break
                for x in range(max(0, nodes[i]), min(self.width, nodes[i + 1] + 1)):
                    self.set(x, y, color)

    def text(self, x: int, y: int, text: str, scale: int, color: Color, tracking: int = 1) -> None:
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            width = max(len(row) for row in glyph)
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + gx * scale, y + gy * scale, cx + (gx + 1) * scale, y + (gy + 1) * scale, color)
            cx += (width + tracking) * scale

    def downsample(self, factor: int) -> "Canvas":
        out = Canvas(self.width // factor, self.height // factor)
        for oy in range(out.height):
            for ox in range(out.width):
                acc = [0, 0, 0, 0]
                count = factor * factor
                for sy in range(factor):
                    for sx in range(factor):
                        p = self.pixels[(oy * factor + sy) * self.width + (ox * factor + sx)]
                        for i in range(4):
                            acc[i] += p[i]
                out.pixels[oy * out.width + ox] = tuple(round(v / count) for v in acc)  # type: ignore[assignment]
        return out

    def save_png(self, path: Path) -> None:
        raw = bytearray()
        for y in range(self.height):
            raw.append(0)
            for x in range(self.width):
                raw.extend(self.pixels[y * self.width + x])
        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)


def draw_icon(size: int) -> Canvas:
    scale = 4
    c = Canvas(size * scale, size * scale)
    s = scale
    cx = cy = size * s // 2
    c.circle(cx + 8 * s, cy + 10 * s, 108 * s, SHADOW)
    c.circle(cx, cy, 108 * s, YELLOW)
    c.circle(cx, cy, 94 * s, WHITE)
    c.circle(cx, cy, 86 * s, YELLOW)
    c.rounded_rect(58 * s, 84 * s, 198 * s, 184 * s, 12 * s, DARK)
    c.rounded_rect(78 * s, 104 * s, 178 * s, 164 * s, 8 * s, (65, 65, 65, 255))
    c.polygon([(128 * s, 42 * s), (166 * s, 110 * s), (138 * s, 98 * s), (150 * s, 142 * s), (108 * s, 142 * s), (120 * s, 100 * s), (92 * s, 112 * s)], RED)
    c.polygon([(128 * s, 70 * s), (146 * s, 112 * s), (132 * s, 104 * s), (138 * s, 130 * s), (116 * s, 130 * s), (122 * s, 106 * s), (110 * s, 114 * s)], YELLOW)
    c.text(74 * s, 188 * s, "HV20", 8 * s, RED, tracking=1)
    return c.downsample(scale)


def draw_logo(width: int, height: int) -> Canvas:
    scale = 3
    c = Canvas(width * scale, height * scale)
    s = scale
    c.rounded_rect(4 * s, 12 * s, (width - 4) * s, (height - 12) * s, 18 * s, YELLOW)
    c.rounded_rect(14 * s, 22 * s, 104 * s, 106 * s, 12 * s, WHITE)
    c.rounded_rect(26 * s, 44 * s, 92 * s, 84 * s, 5 * s, DARK)
    c.polygon([(59 * s, 24 * s), (82 * s, 64 * s), (65 * s, 58 * s), (73 * s, 82 * s), (47 * s, 82 * s), (55 * s, 58 * s), (38 * s, 66 * s)], RED)
    c.text(144 * s, 36 * s, "HV20", 10 * s, RED, tracking=1)
    return c.downsample(scale)


def main() -> None:
    BRAND.mkdir(parents=True, exist_ok=True)
    draw_icon(256).save_png(BRAND / "icon.png")
    draw_logo(512, 128).save_png(BRAND / "logo.png")
    print(BRAND / "icon.png")
    print(BRAND / "logo.png")


if __name__ == "__main__":
    main()
