#!/usr/bin/env python3
"""make.fun food-picture-01 entry: draws a photorealistic-style burger illustration to /output/entry.png."""
import os
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
OUT = os.environ.get("MF_OUT", "/output/entry.png")

def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)

def build():
    img = Image.new("RGB", (W, H), (24, 20, 28))
    d = ImageDraw.Draw(img)
    # radial warm glow backdrop
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([120, 120, 904, 904], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.composite(Image.new("RGB", (W, H), (86, 48, 30)), img, glow)
    d = ImageDraw.Draw(img)

    cx = 512
    # shadow under the burger
    sh = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sh)
    sd.ellipse([220, 800, 804, 880], fill=90)
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, sh)
    d = ImageDraw.Draw(img)

    # top bun (dome)
    d.ellipse([240, 300, 784, 620], fill=(226, 152, 74))
    d.ellipse([270, 318, 754, 570], fill=(240, 172, 92))
    # sesame seeds
    import math
    for (sx, sy, ang) in [(330,430,20),(420,390,-15),(510,370,10),(600,395,-25),(670,440,15),
                          (370,500,-20),(470,470,25),(560,480,-10),(650,505,20),
                          (300,540,10),(420,555,-20),(540,565,15),(660,560,-15)]:
        a = math.radians(ang)
        dx, dy = 14*math.cos(a), 8*math.sin(a)
        d.ellipse([sx-dx, sy-abs(dy)-1, sx+dx, sy+abs(dy)+1], fill=(246, 226, 178))

    # lettuce ruffle
    for i, x in enumerate(range(260, 780, 26)):
        r = 22 if i % 2 == 0 else 14
        d.ellipse([x, 600, x+52, 600+r+34], fill=(120, 190, 88))
    d.rectangle([272, 618, 768, 646], fill=(110, 176, 80))

    # cheese
    d.polygon([(300, 646), (724, 646), (744, 682), (280, 682)], fill=(251, 186, 46))
    for (x1, x2) in [(330, 470), (500, 630)]:
        d.polygon([(x1, 682), (x2, 682), (x2-24, 706), (x1-18, 706)], fill=(253, 200, 70))

    # patty
    rounded(d, [272, 672, 752, 748], 36, (122, 70, 42))
    rounded(d, [290, 688, 734, 726], 20, (146, 88, 52))
    # grill marks
    for gx in range(320, 710, 60):
        d.line([gx, 690, gx+34, 726], fill=(96, 54, 32), width=7)

    # tomato slices peeking
    d.ellipse([300, 730, 380, 764], fill=(214, 62, 52))
    d.ellipse([640, 730, 720, 764], fill=(214, 62, 52))

    # bottom bun
    rounded(d, [264, 748, 760, 830], 44, (222, 148, 72))
    rounded(d, [284, 764, 740, 806], 30, (236, 166, 88))

    # steam wisps
    steam = ImageDraw.Draw(img)
    for sx in (430, 512, 594):
        for k, (ox, oy, rw) in enumerate([(0, 0, 16), (10, -40, 13), (-8, -80, 10)]):
            steam.arc([sx+ox-rw, 210+oy, sx+ox+rw, 290+oy], 300, 60, fill=(255, 255, 255), width=5)

    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def main():
    img = build()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
