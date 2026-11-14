#!/usr/bin/env python3
"""make.fun food-picture-01 entry: draws a warm burger illustration to /output/entry.png.

Pure Python standard library only (no Pillow): a small framebuffer renders the
scene and writes the PNG bytes directly with zlib + struct. Deterministic.
"""
import math
import os
import struct
import zlib

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


class FB:
    """A tiny RGB framebuffer with primitive shape fills and PNG export."""

    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w = w
        self.h = h
        self.px = [list(bg) for _ in range(w * h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = list(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.set(x, y, c)

    def fill_ellipse(self, cx, cy, rx, ry, c):
        rx = max(1, int(rx))
        ry = max(1, int(ry))
        for y in range(cy - ry, cy + ry + 1):
            if not (0 <= y < self.h):
                continue
            dy = (y - cy) / ry
            span = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            x0 = max(0, int(cx - span))
            x1 = min(self.w, int(cx + span) + 1)
            base = y * self.w
            for x in range(x0, x1):
                self.px[base + x] = list(c)

    def thick_line(self, x0, y0, x1, y1, width, c):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, width // 2)
        for i in range(steps + 1):
            t = i / steps
            self.fill_ellipse(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, r, c)

    def arc(self, cx, cy, r, a0deg, a1deg, width, c, steps=None):
        steps = steps or max(int(abs(a1deg - a0deg) * r / 2), 24)
        rr = max(1, width // 2)
        a0 = math.radians(a0deg)
        a1 = math.radians(a1deg)
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.fill_ellipse(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), rr, rr, c)

    def polygon(self, pts, c):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if y1 == y2:
                    continue
                if min(y1, y2) <= y + 0.5 < max(y1, y2):
                    xs.append(x1 + (y + 0.5 - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[i])), min(self.w, int(xs[i + 1]) + 1)):
                    self.set(x, y, c)

    # ---- soft-look helpers (hand-rolled in place of Pillow blur) ----

    def radial_glow(self, cx, cy, r, color, strength):
        """Alpha-blended glow disc fading with distance."""
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy2 = (y - cy) * (y - cy)
            row = y * self.w
            for x in range(max(0, cx - r), min(self.w, cx + r + 1)):
                d2 = (x - cx) * (x - cx) + dy2
                if d2 > r * r:
                    continue
                a = strength * (1.0 - math.sqrt(d2) / r)
                if a <= 0:
                    continue
                base = self.px[row + x]
                self.px[row + x] = [
                    min(255, int(base[k] + (color[k] - base[k]) * a)) for k in range(3)
                ]

    def soft_shadow(self, cx, cy, rx, ry, strength=0.55):
        """Fake blurred ellipse shadow via squared falloff."""
        ex, ey = rx + rx // 3, ry + ry // 3
        for y in range(max(0, cy - ey), min(self.h, cy + ey + 1)):
            dy = y - cy
            row = y * self.w
            for x in range(max(0, cx - ex), min(self.w, cx + ex + 1)):
                dx = x - cx
                e = (dx / max(1, ex)) ** 2 + (dy / max(1, ey)) ** 2
                if e > 1.0:
                    continue
                a = strength * (1.0 - math.sqrt(e)) ** 2
                if a <= 0:
                    continue
                base = self.px[row + x]
                self.px[row + x] = [max(0, int(base[k] * (1 - a))) for k in range(3)]

    def save_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            for (r, g, b) in self.px[y * self.w:(y + 1) * self.w]:
                raw += bytes((r, g, b))
        comp = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", comp)
        png += chunk(b"IEND", b"")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)


def build():
    fb = FB(W, H, (24, 20, 28))

    # warm radial glow backdrop (stacked discs, soft falloff)
    for (r, s) in [(470, 0.10), (400, 0.14), (330, 0.16), (260, 0.14)]:
        fb.radial_glow(512, 520, r, (96, 56, 34), s)

    # soft shadow under the burger
    fb.soft_shadow(512, 852, 300, 42, 0.6)

    cx = 512

    # ---- top bun: dome built from stacked ellipses for shading ----
    for i, (ry, col) in enumerate([
        (170, (206, 136, 62)),
        (160, (222, 152, 74)),
        (146, (236, 166, 86)),
        (128, (244, 178, 96)),
    ]):
        fb.fill_ellipse(cx, 500 - i * 4, 272 - i * 6, ry, col)
    fb.fill_rect(240, 560, 784, 612, (236, 166, 86))

    # highlight sheen on the dome (upper-left)
    fb.radial_glow(cx - 90, 350, 120, (252, 214, 150), 0.35)
    fb.radial_glow(cx - 40, 320, 150, (252, 214, 150), 0.25)

    # sesame seeds: small tilted ellipses with a darker rim for depth
    seeds = [
        (330, 430, 20), (420, 390, -15), (510, 368, 10), (600, 395, -25),
        (672, 440, 15), (368, 498, -20), (470, 470, 25), (560, 480, -10),
        (650, 505, 20), (300, 540, 10), (420, 552, -20), (540, 565, 15),
        (660, 558, -15), (740, 520, 12),
    ]
    for (sx, sy, ang) in seeds:
        a = math.radians(ang)
        dx, dy = 15 * math.cos(a), 9 * math.sin(a)
        fb.fill_ellipse(sx, sy, abs(dx) + 3, abs(dy) + 3, (214, 186, 138))
        fb.fill_ellipse(sx - 1, sy - 1, abs(dx), abs(dy), (246, 228, 182))

    # ---- lettuce ruffle: alternating bumps ----
    for i, x in enumerate(range(248, 784, 26)):
        r = 24 if i % 2 == 0 else 15
        col = (128, 200, 92) if i % 2 == 0 else (110, 182, 80)
        fb.fill_ellipse(x + 13, 606, 30, r, col)
    fb.fill_rect(268, 616, 756, 644, (112, 178, 82))

    # ---- cheese: melted drape with drips ----
    fb.polygon([(296, 640), (728, 640), (752, 680), (272, 680)], (248, 182, 42))
    for (x1, x2) in [(320, 452), (500, 632), (676, 742)]:
        fb.polygon([(x1, 678), (x2, 678), (x2 - 26, 712), (x1 - 14, 712)], (252, 198, 66))
    fb.thick_line(300, 644, 724, 644, 5, (255, 214, 96))

    # ---- patty ----
    fb.fill_ellipse(512, 700, 244, 44, (112, 62, 36))
    fb.fill_ellipse(512, 694, 232, 36, (140, 84, 48))
    fb.fill_ellipse(512, 690, 210, 26, (152, 94, 54))
    # grill marks (double strokes for depth)
    for gx in range(330, 700, 62):
        fb.thick_line(gx, 678, gx + 34, 718, 8, (96, 52, 30))
        fb.thick_line(gx + 6, 678, gx + 40, 718, 3, (120, 70, 42))
    # char speckle on patty top
    for (px_, py_) in [(360, 668), (420, 662), (480, 666), (545, 660), (610, 665), (668, 670)]:
        fb.fill_ellipse(px_, py_, 6, 4, (88, 48, 28))

    # ---- tomato slices peeking out ----
    for (tx, w_) in [(330, 84), (640, 84)]:
        fb.fill_ellipse(tx + w_ // 2, 726, w_ // 2, 20, (198, 52, 46))
        fb.fill_ellipse(tx + w_ // 2, 724, w_ // 2 - 10, 13, (222, 74, 62))

    # ---- bottom bun ----
    fb.fill_ellipse(512, 800, 252, 46, (206, 134, 62))
    fb.fill_rect(260, 760, 764, 806, (222, 148, 72))
    fb.fill_ellipse(512, 806, 244, 40, (236, 166, 88))
    fb.thick_line(300, 836, 724, 836, 6, (176, 108, 52))

    # ---- steam wisps: fading glow dots along arcs, deterministic ----
    for sx in (432, 512, 592):
        for k, (ox, oy, rw) in enumerate([(0, 0, 16), (10, -46, 13), (-8, -92, 10)]):
            for i in range(27):
                a = math.radians(300 + (120 * i / 26))
                x = sx + ox + rw * math.cos(a)
                y = 240 + oy + 42 * math.sin(a)
                fb.radial_glow(int(x), int(y), 9, (255, 255, 255), 0.30 * (i / 26))

    # final soft vignette so edges recede
    fb.radial_glow(512, 512, 760, (12, 10, 14), 0.10)

    return fb


def main():
    out = os.path.join(OUT, "entry.png")
    fb = build()
    fb.save_png(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
