"""Pərdə promo video v2: 1920x1080, 30 fps, beat-synced, with a synthesized soundtrack.

Usage: python tools/video/render_v2.py <repo> <out.mp4> [preview times...]
Every masked string shown is produced by the real masking engine at render time.
"""
import math
import random
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import qrcode
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])
sys.path.insert(0, str(REPO))
from perde import mask  # noqa: E402
import imageio_ffmpeg  # noqa: E402

W, H, FPS = 1920, 1080, 30
BPM = 120
BEAT = 60 / BPM
DUR = 60.0
DROP = 12.0  # logo reveal, the music drops here

FONTS = Path(r"C:\Windows\Fonts")
BLACK = str(FONTS / "seguibl.ttf")
BOLD = str(FONTS / "segoeuib.ttf")
LIGHT = str(FONTS / "segoeuisl.ttf")
MONO = str(FONTS / "CascadiaMono.ttf")

INK = (10, 14, 24)
INK2 = (18, 26, 44)
PANEL = (24, 35, 58)
LIGHTC = (245, 241, 232)
MUTED = (160, 172, 192)
RED = (240, 72, 86)
AMBER = (246, 170, 90)
GREEN = (110, 214, 170)
CYAN = (90, 200, 250)

_fc = {}


def F(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def mix(a, b, t):
    t = clamp(t)
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


# --- backgrounds and effects -------------------------------------------------

_rng = np.random.default_rng(3)
GRAIN = [Image.fromarray((_rng.normal(0, 7, (H, W)).clip(-20, 20) + 128).astype(np.uint8), "L") for _ in range(4)]


def background(t, tint=INK2):
    """Dark radial gradient that slowly drifts."""
    img = Image.new("RGB", (W, H), INK)
    g = Image.new("L", (W // 8, H // 8))
    cx = W // 16 + int(40 * math.sin(t * 0.3))
    cy = H // 16 + int(25 * math.cos(t * 0.25))
    arr = np.zeros((H // 8, W // 8), np.float32)
    yy, xx = np.mgrid[0:H // 8, 0:W // 8]
    arr = np.clip(1 - np.hypot(xx - cx, yy - cy) / (W // 10), 0, 1) * 255
    g = Image.fromarray(arr.astype(np.uint8), "L").resize((W, H), Image.BILINEAR)
    img.paste(Image.new("RGB", (W, H), tint), (0, 0), g)
    return img


def grain(img, t):
    g = GRAIN[int(t * FPS) % 4]
    return Image.blend(img, ImageChops.overlay(img, Image.merge("RGB", (g, g, g))), 0.35)


def glow_text(img, xy, s, font, fill, glow=None, radius=18, alpha=1.0):
    """Text with a soft glow behind it."""
    if alpha <= 0:
        return
    glow = glow or fill
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, s, font=font, fill=glow)
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    img.paste(ImageChops.add(img, Image.eval(blur, lambda v: int(v * 0.8 * alpha))))
    ImageDraw.Draw(img).text(xy, s, font=font, fill=mix(INK, fill, alpha))


def center_x(s, font):
    return (W - font.getlength(s)) / 2


def glitch(img, amount, t):
    """RGB split plus horizontal slice jitter."""
    if amount <= 0:
        return img
    r, g, b = img.split()
    off = int(18 * amount)
    r = ImageChops.offset(r, off, 0)
    b = ImageChops.offset(b, -off, 0)
    out = Image.merge("RGB", (r, g, b))
    rnd = random.Random(int(t * 60))
    for _ in range(int(8 * amount)):
        y = rnd.randrange(0, H - 40)
        h = rnd.randrange(8, 40)
        strip = out.crop((0, y, W, y + h))
        out.paste(strip, (rnd.randrange(-80, 80), y))
    return out


def punch(img, amount):
    """Zoom punch: scale the frame up around the centre."""
    if amount <= 0.001:
        return img
    s = 1 + 0.06 * amount
    w, h = int(W / s), int(H / s)
    x, y = (W - w) // 2, (H - h) // 2
    return img.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)


def flash(img, amount, col=(255, 255, 255)):
    if amount <= 0:
        return img
    return Image.blend(img, Image.new("RGB", (W, H), col), clamp(amount))


# --- content from the real engine --------------------------------------------

MSG = ("Salam, mən Nərmin Quliyeva. Kartımdan 2 dəfə 150 AZN çıxılıb, kart 4111 1111 1111 1111. "
       "FIN kodum 6TR9K2L, hesabım AZ21NABZ00000000137010001944. Zəng edin: 055 412 33 90.")
RES = mask(MSG)
SPANS = RES.spans
MSG_FONT = F(MONO, 42)


def layout(text, font, max_w, x0, y0, lh):
    out, x, y, i = [], x0, y0, 0
    sp = font.getlength(" ")
    for word in text.split(" "):
        ww = font.getlength(word)
        if x + ww > x0 + max_w and x > x0:
            x, y = x0, y + lh
        for ch in word:
            out.append((x, y, ch, i))
            x += font.getlength(ch)
            i += 1
        out.append((x, y, " ", i))
        x += sp
        i += 1
    return out


BOX = (170, 330, 1750, 640)
LAY = layout(MSG, MSG_FONT, 1500, 210, 365, 66)
LAY_MASKED = layout(RES.masked, MSG_FONT, 1500, 210, 365, 66)
TAG_IDX = [(m.start(), m.end()) for m in re.finditer(r"\[[A-Z_]+_\d+\]", RES.masked)]


def span_k(i):
    for k, s in enumerate(SPANS):
        if s.start <= i < s.end:
            return k
    return None


def span_center(k):
    pts = [(x, y) for x, y, _, i in LAY if SPANS[k].start <= i < SPANS[k].end]
    return (sum(p[0] for p in pts) / len(pts) + 10, sum(p[1] for p in pts) / len(pts) + 26)


# demo scenarios written by the team (demo_texts/), masked live
DEMOS = []
for p in sorted((REPO / "demo_texts").glob("*.txt")):
    txt = p.read_text(encoding="utf-8").strip().replace("\n", " ")
    r = mask(txt)
    DEMOS.append((p.stem, r.masked[:150], len(r.spans)))
DEMO_VALUES = sum(n for _, _, n in DEMOS)

APP = Image.open(HERE / "shots" / "02_after_send.png").convert("RGB")

QR = qrcode.make("https://huggingface.co/spaces/Traxic/perde", box_size=10, border=2).convert("RGB").resize((300, 300), Image.NEAREST)

# --- scenes -----------------------------------------------------------------


def s_cold_open(t):
    """0-3s: glitchy hook."""
    img = background(t)
    f = F(BLACK, 110)
    a = "Your customer's data"
    b = "just left the country."
    glow_text(img, (center_x(a, f), 330), a, f, LIGHTC, alpha=ease(t / 0.3))
    if t > 1.0:
        glow_text(img, (center_x(b, f), 480), b, f, RED, alpha=ease((t - 1.0) / 0.2))
    g = 0.0
    for hit in (0.0, 1.0, 2.5):
        if hit <= t < hit + 0.25:
            g = 1 - (t - hit) / 0.25
    return glitch(img, g, t)


def s_leak(t):
    """3-10s: message types, scanner finds data, data flies to a foreign server."""
    img = background(t + 3)
    d = ImageDraw.Draw(img)
    cap = "A bank clerk pastes a complaint into a chatbot…"
    d.text((center_x(cap, F(BOLD, 52)), 190), cap, font=F(BOLD, 52), fill=mix(INK, LIGHTC, ease(t / 0.4)))
    d.rounded_rectangle(BOX, 26, fill=PANEL, outline=(52, 70, 104), width=2)
    typed = int(len(MSG) * clamp((t - 0.3) / 2.2))
    scan_x = BOX[0] + (BOX[2] - BOX[0]) * clamp((t - 2.7) / 1.2)
    for x, y, ch, i in LAY:
        if i >= typed:
            break
        k = span_k(i)
        col = (220, 228, 240)
        if k is not None and x < scan_x:
            col = RED
            d.rectangle((x, y + 54, x + MSG_FONT.getlength(ch), y + 58), fill=RED)
        fly = clamp((t - (4.2 + 0.25 * k)) / 0.9) if k is not None else 0
        if fly > 0:
            col = mix(col, PANEL, fly)
        d.text((x, y), ch, font=MSG_FONT, fill=col)
    if 2.7 <= t <= 3.9:
        layer = Image.new("RGB", (W, H))
        ImageDraw.Draw(layer).rectangle((scan_x - 6, BOX[1], scan_x + 6, BOX[3]), fill=CYAN)
        img = ImageChops.add(img, layer.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(img)
        d.rectangle((scan_x - 2, BOX[1], scan_x + 2, BOX[3]), fill=CYAN)
    # the "server" the data flies to
    sx, sy = 1560, 860
    on = ease((t - 4.0) / 0.4)
    if on > 0:
        d.rounded_rectangle((sx - 220, sy - 70, sx + 220, sy + 70), 18, fill=mix(INK, (60, 20, 30), on), outline=mix(INK, RED, on), width=3)
        d.text((sx - 190, sy - 40), "FOREIGN AI SERVER", font=F(BOLD, 34), fill=mix(INK, RED, on))
        left = sum(1 for k in range(len(SPANS)) if t > 4.2 + 0.25 * k + 0.9)
        d.text((sx - 190, sy + 4), f"{left} personal values received", font=F(LIGHT, 28), fill=mix(INK, LIGHTC, on))
    for k in range(len(SPANS)):
        p = clamp((t - (4.2 + 0.25 * k)) / 0.9)
        if 0 < p < 1:
            x0, y0 = span_center(k)
            q = ease(p)
            x = x0 + (sx - x0) * q
            y = y0 + (sy - y0) * q - 220 * math.sin(math.pi * q)
            for j in range(10):
                tt = clamp(q - j * 0.025)
                px = x0 + (sx - x0) * tt
                py = y0 + (sy - y0) * tt - 220 * math.sin(math.pi * tt)
                r = 9 - j * 0.7
                d.ellipse((px - r, py - r, px + r, py + r), fill=mix(INK, RED, 1 - j / 10))
            d.text((x + 14, y - 18), SPANS[k].entity, font=F(BOLD, 26), fill=LIGHTC)
    if t > 6.0:
        a = ease((t - 6.0) / 0.4)
        s = f"{len(SPANS)} pieces of personal data. Gone."
        glow_text(img, (center_x(s, F(BLACK, 64)), 700), s, F(BLACK, 64), RED, alpha=a)
    return img


def s_question(t):
    """10-12s."""
    img = background(t, (40, 16, 28))
    f = F(BLACK, 128)
    s = 1 + 0.05 * t
    a, b = "What if the AI", "never saw it?"
    glow_text(img, (center_x(a, f), 360), a, f, LIGHTC, alpha=ease(t / 0.25))
    if t > 0.7:
        glow_text(img, (center_x(b, f), 520), b, f, RED, alpha=ease((t - 0.7) / 0.2))
    return punch(img, 0.6 * s - 0.6)


def s_logo(t):
    """12-16s: curtain slams down on the drop, logo reveal."""
    img = background(t, (36, 14, 26))
    d = ImageDraw.Draw(img)
    n = 14
    sw = W / n
    if t < 0.7:
        for k in range(n):
            p = ease((t - k * 0.02) / 0.35)
            d.rectangle((k * sw, 0, (k + 1) * sw + 1, H * p), fill=mix(RED, AMBER, k / n))
        return img
    for k, op in enumerate([1, 0.6, 0.35, 0.18, 0.08]):
        x = 1600 + k * 60
        d.rectangle((x, 0, x + 28, H), fill=mix(INK, mix(RED, AMBER, 0.35), op))
    f = F(BLACK, 260)
    sc = ease_back((t - 0.7) / 0.5)
    glow_text(img, (170, 300 + 40 * (1 - sc)), "Pərdə", f, LIGHTC, glow=RED, radius=30, alpha=clamp(sc))
    if t > 1.3:
        a = ease((t - 1.3) / 0.4)
        d = ImageDraw.Draw(img)
        d.text((180, 640), "the curtain between your customers", font=F(LIGHT, 54), fill=mix(INK, MUTED, a))
        d.text((180, 715), "and the cloud", font=F(LIGHT, 54), fill=mix(INK, MUTED, a))
    img = flash(img, 1 - clamp((t - 0.7) / 0.35))
    return punch(img, 1 - clamp((t - 0.7) / 0.5))


def s_mask(t):
    """16-22s: scanner turns every value into a tag."""
    img = background(t)
    d = ImageDraw.Draw(img)
    s = "Pərdə masks it on your own machine."
    d.text((center_x(s, F(BOLD, 56)), 190), s, font=F(BOLD, 56), fill=mix(INK, LIGHTC, ease(t / 0.4)))
    d.rounded_rectangle(BOX, 26, fill=PANEL, outline=(52, 70, 104), width=2)
    scan = clamp((t - 0.6) / 1.8)
    scan_x = BOX[0] + (BOX[2] - BOX[0]) * scan
    if scan < 1:
        for x, y, ch, i in LAY:
            k = span_k(i)
            col = (220, 228, 240) if k is None else (RED if x > scan_x else GREEN)
            d.text((x, y), ch, font=MSG_FONT, fill=col)
        layer = Image.new("RGB", (W, H))
        ImageDraw.Draw(layer).rectangle((scan_x - 6, BOX[1], scan_x + 6, BOX[3]), fill=GREEN)
        img = ImageChops.add(img, layer.filter(ImageFilter.GaussianBlur(12)))
    else:
        q = ease((t - 2.4) / 0.5)
        for x, y, ch, i in LAY_MASKED:
            is_tag = any(a <= i < b for a, b in TAG_IDX)
            d.text((x, y), ch, font=MSG_FONT, fill=mix(PANEL, GREEN, q) if is_tag else (220, 228, 240))
    if t > 3.2:
        a = ease((t - 3.2) / 0.4)
        s = "The AI provider receives only tags."
        glow_text(img, (center_x(s, F(BLACK, 60)), 700), s, F(BLACK, 60), GREEN, alpha=a)
        s2 = "Real values stay inside. The answer is restored locally."
        ImageDraw.Draw(img).text((center_x(s2, F(LIGHT, 40)), 800), s2, font=F(LIGHT, 40), fill=mix(INK, MUTED, ease((t - 3.8) / 0.4)))
    return img


CAMERA = [  # (t, x, y, w, caption)
    (0.0, 0, 0, 1920, None),
    (1.6, 360, 580, 540, "1 · Detected on your device"),
    (4.6, 852, 580, 540, "2 · The AI sees only tags"),
    (7.6, 1344, 580, 540, "3 · Answer restored locally"),
    (10.2, 360, 540, 1500, "Leak check passed · 6 values masked"),
]


def s_app(t):
    """22-34s: real app, browser frame, camera moves."""
    img = background(t)
    for k in range(len(CAMERA) - 1, -1, -1):
        if t >= CAMERA[k][0]:
            break
    t0, x1, y1, w1, cap = CAMERA[k]
    _, x0, y0, w0, _ = CAMERA[k - 1] if k else CAMERA[k]
    q = ease((t - t0) / 0.9)
    x, y, w = x0 + (x1 - x0) * q, y0 + (y1 - y0) * q, w0 + (w1 - w0) * q
    h = w * 9 / 16
    x, y = clamp(x, 0, 1920 - w), clamp(y, 0, 1080 - h)
    view = APP.crop((int(x), int(y), int(x + w), int(y + h))).resize((1600, 900), Image.BILINEAR)
    fx, fy = 160, 110
    shadow = Image.new("RGB", (W, H))
    ImageDraw.Draw(shadow).rounded_rectangle((fx - 10, fy - 30, fx + 1610, fy + 930), 26, fill=(0, 0, 0))
    img = ImageChops.subtract(img, shadow.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((fx, fy - 46, fx + 1600, fy + 900), 18, fill=(36, 40, 52))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((fx + 22 + i * 30, fy - 32, fx + 40 + i * 30, fy - 14), fill=c)
    d.rounded_rectangle((fx + 140, fy - 38, fx + 900, fy - 8), 10, fill=(24, 28, 38))
    d.text((fx + 160, fy - 37), "huggingface.co/spaces/Traxic/perde", font=F(LIGHT, 22), fill=MUTED)
    img.paste(view, (fx, fy))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((fx + 1290, fy + 20, fx + 1580, fy + 70), 25, fill=RED)
    d.text((fx + 1316, fy + 26), "● REAL APP · LIVE", font=F(BOLD, 28), fill=LIGHTC)
    if cap:
        a = ease((t - t0 - 0.5) / 0.35)
        f = F(BLACK, 56)
        bw = f.getlength(cap) + 90
        d.rounded_rectangle(((W - bw) / 2, 930 + 30 * (1 - a), (W + bw) / 2, 1040 + 30 * (1 - a)), 28, fill=mix(INK, (14, 18, 30), a), outline=mix(INK, GREEN, a), width=3)
        d.text(((W - bw) / 2 + 45, 945 + 30 * (1 - a)), cap, font=f, fill=mix(INK, LIGHTC, a))
    beat_p = (t % (BEAT * 4)) / (BEAT * 4)
    return punch(img, 0.25 * max(0, 1 - beat_p * 8))


def s_montage(t):
    """34-40s: the team's 56 demo scenarios, masked live."""
    img = background(t, (14, 30, 36))
    d = ImageDraw.Draw(img)
    n_show = min(len(DEMOS), int(t / 5.2 * len(DEMOS)) + 1)
    cols, rows = 4, 3
    cw, ch = 400, 190
    x0, y0 = (W - cols * cw - (cols - 1) * 24) / 2, 230
    for slot in range(cols * rows):
        idx = n_show - 1 - slot
        if idx < 0:
            continue
        name, txt, n = DEMOS[idx]
        r, c = divmod(slot, cols)
        x, y = x0 + c * (cw + 24), y0 + r * (ch + 24)
        fresh = slot == 0
        d.rounded_rectangle((x, y, x + cw, y + ch), 16, fill=PANEL, outline=GREEN if fresh else (52, 70, 104), width=3 if fresh else 2)
        d.text((x + 18, y + 12), name.replace("_", " ")[:30], font=F(BOLD, 22), fill=AMBER)
        f = F(MONO, 17)
        line, yy = "", y + 48
        for word in txt.split(" "):
            if f.getlength(line + word) > cw - 36:
                d.text((x + 18, yy), line, font=f, fill=(210, 220, 235))
                line, yy = "", yy + 24
                if yy > y + ch - 30:
                    break
            line += word + " "
        if yy <= y + ch - 30:
            d.text((x + 18, yy), line, font=f, fill=(210, 220, 235))
        for m in re.finditer(r"\[[A-Z_]+_\d+\]", txt[:90]):
            pass
    head = f"{n_show} demo scenarios · AZ · RU · EN · masked live"
    glow_text(img, (center_x(head, F(BLACK, 58)), 100), head, F(BLACK, 58), LIGHTC, glow=GREEN, alpha=ease(t / 0.3))
    if t > 3.5:
        s = f"{DEMO_VALUES} personal values found in {len(DEMOS)} team-written scenarios"
        d = ImageDraw.Draw(img)
        d.text((center_x(s, F(BOLD, 40)), 960), s, font=F(BOLD, 40), fill=mix(INK, GREEN, ease((t - 3.5) / 0.4)))
    return img


def ring(d, cx, cy, r, w, frac, col, track=(40, 52, 76)):
    d.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=track, width=w)
    if frac > 0:
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=col, width=w)


def s_stats(t):
    """40-48s: measured result."""
    img = background(t, (36, 14, 26))
    d = ImageDraw.Draw(img)
    s = "Tested on 1,000 Azerbaijani texts it had never seen"
    d.text((center_x(s, F(BOLD, 50)), 90), s, font=F(BOLD, 50), fill=mix(INK, LIGHTC, ease(t / 0.4)))
    p1 = ease((t - 0.5) / 2.0)
    p2 = ease((t - 0.9) / 2.0)
    layer = Image.new("RGB", (W, H))
    ring(ImageDraw.Draw(layer), 620, 560, 290, 46, 0.949 * p1, RED)
    img = ImageChops.add(img, layer.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    ring(d, 620, 560, 290, 46, 0.949 * p1, RED)
    ring(d, 1340, 560, 200, 34, 0.239 * p2, MUTED)
    v1 = f"{94.9 * p1:.1f}%"
    glow_text(img, (620 - F(BLACK, 120).getlength(v1) / 2, 470), v1, F(BLACK, 120), LIGHTC, glow=RED)
    d = ImageDraw.Draw(img)
    d.text((620 - F(BOLD, 40).getlength("Pərdə") / 2, 610), "Pərdə", font=F(BOLD, 40), fill=RED)
    v2 = f"{23.9 * p2:.1f}%"
    d.text((1340 - F(BLACK, 80).getlength(v2) / 2, 495), v2, font=F(BLACK, 80), fill=LIGHTC)
    d.text((1340 - F(BOLD, 32).getlength("generic filter") / 2, 590), "generic filter", font=F(BOLD, 32), fill=MUTED)
    if t > 3.2:
        a = ease((t - 3.2) / 0.4)
        s = "of personal data protected"
        d.text((center_x(s, F(LIGHT, 44)), 900), s, font=F(LIGHT, 44), fill=mix(INK, MUTED, a))
    if t > 4.4:
        a = ease((t - 4.4) / 0.4)
        f = F(BLACK, 58)
        parts = [("Leak rate:  ", LIGHTC), ("100% raw", RED), ("  →  ", MUTED), ("76.1% filter", AMBER), ("  →  ", MUTED), ("5.1% Pərdə", GREEN)]
        x = (W - sum(f.getlength(p) for p, _ in parts)) / 2
        for p, c in parts:
            d.text((x, 965), p, font=f, fill=mix(INK, c, a))
            x += f.getlength(p)
    hit = 1 - clamp((t - 2.5) / 0.3) if t > 2.5 else 0
    return punch(img, hit)


CHIPS = ["FIN 6TR9K2L", "VÖEN", "AZ IBAN", "+994", "AZE / AA ID", "oğlu · qızı", "Rənanın", "Кириллица", "Docker", "Grok · OpenAI · Gemini", "Gemma via llama.cpp", "0.14 ms"]


def s_chips(t):
    """48-53s."""
    img = background(t)
    d = ImageDraw.Draw(img)
    s = "Built for Azerbaijani data. Ready to deploy."
    glow_text(img, (center_x(s, F(BLACK, 66)), 140), s, F(BLACK, 66), LIGHTC, alpha=ease(t / 0.3))
    d = ImageDraw.Draw(img)
    f = F(MONO, 42)
    x, y = 170, 320
    for k, c in enumerate(CHIPS):
        w = f.getlength(c) + 70
        if x + w > W - 170:
            x, y = 170, y + 140
        a = ease_back((t - 0.4 - 0.12 * k) / 0.35)
        if a > 0:
            col = GREEN if k >= 8 else RED
            yy = y + 40 * (1 - clamp(a))
            d.rounded_rectangle((x, yy, x + w, yy + 96), 48, fill=mix(INK, PANEL, clamp(a)), outline=mix(INK, col, clamp(a)), width=3)
            d.text((x + 35, yy + 20), c, font=f, fill=mix(INK, LIGHTC, clamp(a)))
        x += w + 26
    s2 = "Runs on-premises · no GPU · audit log with hashes only"
    d.text((center_x(s2, F(LIGHT, 44)), 860), s2, font=F(LIGHT, 44), fill=mix(INK, MUTED, ease((t - 2.4) / 0.4)))
    return img


def s_close(t):
    """53-60s."""
    img = background(t, (36, 14, 26))
    d = ImageDraw.Draw(img)
    if t < 0.6:
        n = 14
        sw = W / n
        for k in range(n):
            p = ease((t - k * 0.02) / 0.3)
            d.rectangle((k * sw, 0, (k + 1) * sw + 1, H * p), fill=mix(RED, AMBER, k / n))
        return img
    for k, op in enumerate([1, 0.6, 0.35, 0.18, 0.08]):
        x = 1660 + k * 50
        d.rectangle((x, 0, x + 24, H), fill=mix(INK, mix(RED, AMBER, 0.35), op))
    glow_text(img, (170, 180), "Let the AI read the request.", F(BLACK, 92), LIGHTC, alpha=ease((t - 0.6) / 0.3))
    glow_text(img, (170, 300), "Never the person.", F(BLACK, 92), RED, alpha=ease((t - 1.1) / 0.3))
    a = ease((t - 1.8) / 0.4)
    if a > 0:
        glow_text(img, (170, 520), "Pərdə", F(BLACK, 150), LIGHTC, glow=RED, alpha=a)
        d = ImageDraw.Draw(img)
        d.text((176, 730), "Try it: huggingface.co/spaces/Traxic/perde", font=F(LIGHT, 44), fill=mix(INK, MUTED, a))
        d.text((176, 800), "NeuroBridge 2026 · Enterprise track", font=F(LIGHT, 36), fill=mix(INK, MUTED, a))
        qr = Image.blend(Image.new("RGB", QR.size, INK), QR, a)
        img.paste(qr, (1280, 560))
        d.text((1325, 872), "scan to try it", font=F(BOLD, 30), fill=mix(INK, LIGHTC, a))
    img = flash(img, 1 - clamp((t - 0.6) / 0.3))
    if t > 6.2:
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), clamp((t - 6.2) / 0.8))
    return img


SCENES = [
    (0.0, 3.0, s_cold_open),
    (3.0, 10.0, s_leak),
    (10.0, 12.0, s_question),
    (12.0, 16.0, s_logo),
    (16.0, 22.0, s_mask),
    (22.0, 34.0, s_app),
    (34.0, 40.0, s_montage),
    (40.0, 48.0, s_stats),
    (48.0, 53.0, s_chips),
    (53.0, DUR, s_close),
]


def frame(t):
    for s, e, fn in SCENES:
        if s <= t < e:
            img = fn(t - s)
            if t - s < 0.12 and s > 0 and fn not in (s_logo, s_close):
                img = flash(img, 0.5 * (1 - (t - s) / 0.12), (0, 0, 0))
            return grain(img, t)
    return Image.new("RGB", (W, H), (0, 0, 0))


# --- soundtrack --------------------------------------------------------------

def soundtrack(path):
    sr = 44100
    n = int(DUR * sr)
    out = np.zeros(n)
    rng = np.random.default_rng(11)

    def add(sig, at, gain=1.0):
        i = int(at * sr)
        j = min(n, i + len(sig))
        if 0 <= i < n:
            out[i:j] += sig[: j - i] * gain

    def tone(freqs, dur, kind="saw", decay=2.0):
        tt = np.arange(int(dur * sr)) / sr
        sig = np.zeros_like(tt)
        for f in freqs:
            if kind == "saw":
                for h in range(1, 7):
                    sig += np.sin(2 * np.pi * f * h * tt) / h
            else:
                sig += np.sin(2 * np.pi * f * tt)
        env = np.minimum(1, tt / 0.02) * np.exp(-tt * decay)
        return sig * env / max(1, len(freqs))

    tt = np.arange(int(0.3 * sr)) / sr
    kick = np.sin(2 * np.pi * (42 + 110 * np.exp(-tt * 28)) * tt) * np.exp(-tt * 8)
    hat = np.diff(np.concatenate([[0], rng.normal(0, 1, int(0.05 * sr))])) * np.exp(-np.arange(int(0.05 * sr)) / sr * 70)
    clap = rng.normal(0, 1, int(0.15 * sr)) * np.exp(-np.arange(int(0.15 * sr)) / sr * 25)
    crash = rng.normal(0, 1, int(2.0 * sr)) * np.exp(-np.arange(int(2.0 * sr)) / sr * 2.2)
    crash = np.diff(np.concatenate([[0], crash]))

    chords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (130.81, 164.81, 196.0), (98.0, 123.47, 146.83)]  # Am F C G
    # intro: drone, ticking, riser
    drone = tone([55.0, 82.41], DROP, kind="sine", decay=0.0) * 0.18
    add(drone, 0)
    for b in np.arange(0, DROP, BEAT / 2):
        add(hat, b, 0.08)
    for b in np.arange(3.0, DROP, BEAT * 2):
        add(kick, b, 0.45)
    rt = np.arange(int(2.0 * sr)) / sr
    riser = rng.normal(0, 1, len(rt)) * (rt / rt[-1]) ** 3
    riser = np.convolve(riser, np.ones(8) / 8, mode="same")
    add(riser, DROP - 2.0, 0.5)
    # glitch zaps in the cold open
    for z in (0.0, 1.0, 2.5):
        zt = np.arange(int(0.2 * sr)) / sr
        add(np.sign(np.sin(2 * np.pi * (900 - 3000 * zt) * zt)) * np.exp(-zt * 18), z, 0.25)
    # drop and main groove
    add(crash, DROP, 0.6)
    add(kick, DROP, 1.0)
    bar = 0
    for b0 in np.arange(DROP, DUR - 2.0, BEAT * 4):
        ch = chords[bar % 4]
        add(tone(ch, BEAT * 4, "saw", decay=0.6) * 0.16, b0)
        for k in range(4):
            bt = b0 + k * BEAT
            add(kick, bt, 0.9)
            add(hat, bt + BEAT / 2, 0.16)
            if k in (1, 3):
                add(clap, bt, 0.22)
            add(tone([ch[0] / 2], BEAT * 0.9, "sine", decay=3.0) * 0.45, bt)
            add(tone([ch[0] / 2], BEAT * 0.4, "sine", decay=6.0) * 0.3, bt + BEAT / 2)
        bar += 1
    # pops when tags appear, impact on the stats hit
    pt = np.arange(int(0.12 * sr)) / sr
    pop = np.sin(2 * np.pi * 1320 * pt) * np.exp(-pt * 35)
    for k in range(len(SPANS)):
        add(pop, 16.0 + 0.6 + 1.8 * (k + 0.5) / len(SPANS), 0.25)
    add(crash, 42.5, 0.45)
    add(crash, 53.0, 0.5)
    fade = np.ones(n)
    fl = int(2.5 * sr)
    fade[-fl:] = np.linspace(1, 0, fl)
    out *= fade
    out = np.tanh(out * 1.2)
    out = out / max(1e-9, np.abs(out).max()) * 0.85
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


def main():
    wav = HERE / "track_v2.wav"
    soundtrack(wav)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUT)],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    total = int(DUR * FPS)
    for i in range(total):
        proc.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 3:
        for ts in sys.argv[3:]:
            frame(float(ts)).save(HERE / f"v2_preview_{ts}.png")
    else:
        main()
