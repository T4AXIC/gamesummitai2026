"""Render the Pərdə promo video (1920x1080, 30 fps, with a synthesized soundtrack)."""
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).parent
REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
sys.path.insert(0, str(REPO))
from perde import mask  # noqa: E402  real masking output, not mocked
import imageio_ffmpeg  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 56.0
FONTS = Path(r"C:\Windows\Fonts")
BOLD = str(FONTS / "segoeuib.ttf")
REG = str(FONTS / "segoeui.ttf")
LIGHT = str(FONTS / "segoeuisl.ttf")
MONO = str(FONTS / "CascadiaMono.ttf")

INK = (15, 23, 36)
PANEL = (24, 35, 58)
LIGHTC = (245, 241, 232)
MUTED = (174, 184, 201)
RED = (232, 80, 91)
AMBER = (242, 166, 90)
GREEN = (127, 200, 169)

_font_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * clamp(t)) for a, b in zip(c1, c2))


def text_center(d, y, s, font, fill, alpha=1.0, bg=INK):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2, y), s, font=font, fill=mix(bg, fill, alpha))


# --- message layout --------------------------------------------------------

MSG = ("Salam, mən Nərmin Quliyeva. Kartımdan 2 dəfə 150 AZN çıxılıb, kart 4111 1111 1111 1111. "
       "FIN kodum 6TR9K2L, hesabım AZ21NABZ00000000137010001944. Zəng edin: 055 412 33 90.")
RES = mask(MSG)
SPANS = RES.spans  # real detections
MASKED = RES.masked


def layout(text, font, max_w, x0, y0, lh):
    """Word-wrap; return list of (x, y, ch, index)."""
    out, x, y = [], x0, y0
    space = font.getlength(" ")
    i = 0
    for word in text.split(" "):
        ww = font.getlength(word)
        if x + ww > x0 + max_w and x > x0:
            x, y = x0, y + lh
        for ch in word:
            out.append((x, y, ch, i))
            x += font.getlength(ch)
            i += 1
        out.append((x, y, " ", i))
        x += space
        i += 1
    return out


MSG_FONT = F(MONO, 40)
MSG_BOX = (180, 330, 1740, 600)
MSG_LAYOUT = layout(MSG, MSG_FONT, 1480, 220, 370, 64)
MASKED_LAYOUT = layout(MASKED, MSG_FONT, 1480, 220, 370, 64)


def span_of(idx):
    for k, s in enumerate(SPANS):
        if s.start <= idx < s.end:
            return k
    return None


def tag_ranges(text):
    import re
    return [(m.start(), m.end()) for m in re.finditer(r"\[[A-Z_]+_\d+\]", text)]


TAGS = tag_ranges(MASKED)

# --- scenes ----------------------------------------------------------------


def scene_hook(img, d, t):
    """0-10s: typed message, then personal data lights up red."""
    cap = "A bank clerk pastes a complaint into a chatbot…"
    n = int(len(cap) * ease(t / 1.2))
    text_center(d, 170, cap[:n], F(BOLD, 60), LIGHTC)
    a = ease((t - 0.6) / 0.5)
    d.rounded_rectangle(MSG_BOX, 28, fill=mix(INK, PANEL, a), outline=mix(INK, (44, 58, 85), a), width=2)
    typed = int(len(MSG) * clamp((t - 1.0) / 3.2))
    for x, y, ch, i in MSG_LAYOUT:
        if i >= typed:
            break
        col = (220, 227, 238)
        k = span_of(i)
        if k is not None:
            on = ease((t - (5.4 + 0.45 * k)) / 0.25)
            col = mix(col, RED, on)
            if on > 0:
                d.rectangle((x, y + 52, x + MSG_FONT.getlength(ch), y + 56), fill=mix(PANEL, RED, on))
        d.text((x, y), ch, font=MSG_FONT, fill=col)
    if typed < len(MSG) and int(t * 4) % 2 == 0 and t > 1:
        cx, cy, _, _ = MSG_LAYOUT[min(typed, len(MSG_LAYOUT) - 1)]
        d.rectangle((cx, cy + 4, cx + 4, cy + 50), fill=AMBER)
    if t > 8.2:
        a = ease((t - 8.2) / 0.5)
        text_center(d, 700, f"{len(SPANS)} pieces of personal data just left the building.", F(BOLD, 56), RED, a)


def scene_question(img, d, t):
    """10-13s."""
    s = 1 + 0.08 * ease(t / 3)
    f = F(BOLD, int(110 * s))
    a = ease(t / 0.4)
    text_center(d, 380 - 20 * (s - 1) * 10, "What if the AI", f, LIGHTC, a)
    text_center(d, 520 - 20 * (s - 1) * 10, "never saw them?", f, RED, ease((t - 0.5) / 0.4))


def curtain(d, t, reverse=False):
    """Vertical crimson-to-amber stripes sweeping across."""
    n = 12
    sw = W / n
    for k in range(n):
        p = ease((t - k * 0.04) / 0.5)
        if reverse:
            p = 1 - p
        h = H * p
        col = mix(RED, AMBER, k / n)
        d.rectangle((k * sw, 0, (k + 1) * sw + 1, h), fill=col)


def scene_logo(img, d, t):
    """13-16s: curtain closes, logo appears."""
    if t < 0.9:
        curtain(d, t)
        return
    d.rectangle((0, 0, W, H), fill=INK)
    for k, op in enumerate([1, 0.6, 0.35, 0.15]):
        x = 1340 + k * 60
        d.rectangle((x, 0, x + 28, H), fill=mix(INK, mix(RED, AMBER, 0.3), op * ease((t - 0.9) / 0.6)))
    a = ease((t - 1.0) / 0.5)
    d.text((180, 330), "Pərdə", font=F(BOLD, 230), fill=mix(INK, LIGHTC, a))
    b = ease((t - 1.5) / 0.5)
    d.text((190, 640), "the curtain between your customers", font=F(LIGHT, 60), fill=mix(INK, MUTED, b))
    d.text((190, 715), "and the cloud.", font=F(LIGHT, 60), fill=mix(INK, MUTED, b))


def scene_morph(img, d, t):
    """16-22s: personal data turns into tags, live."""
    text_center(d, 170, "Personal data becomes tags — on your own machine.", F(BOLD, 56), LIGHTC, ease(t / 0.4))
    d.rounded_rectangle(MSG_BOX, 28, fill=PANEL, outline=(44, 58, 85), width=2)
    p = clamp((t - 0.8) / 3.0)
    if p < 0.5:
        for x, y, ch, i in MSG_LAYOUT:
            k = span_of(i)
            col = RED if k is not None else (220, 227, 238)
            if k is not None and p > 0.08 * k:
                col = mix(RED, PANEL, (p - 0.08 * k) * 8)
            d.text((x, y), ch, font=MSG_FONT, fill=col)
    else:
        q = ease((p - 0.5) * 2.5)
        for x, y, ch, i in MASKED_LAYOUT:
            is_tag = any(a <= i < b for a, b in TAGS)
            col = mix(PANEL, GREEN, q) if is_tag else (220, 227, 238)
            d.text((x, y), ch, font=MSG_FONT, fill=col)
    if t > 4.0:
        a = ease((t - 4.0) / 0.5)
        text_center(d, 700, "The AI provider sees only this.", F(BOLD, 56), GREEN, a)


APP = Image.open(HERE / "shots" / "02_after_send.png").convert("RGB")
# crop rectangles on the 1920x1080 app screenshot: (x, y, w) with 16:9 height
SHOTS = [
    (0.0, (0, 0, 1920), None),
    (2.2, (360, 590, 520), "1 · Detected on your device"),
    (5.2, (852, 590, 520), "2 · The AI sees only tags"),
    (8.2, (1344, 590, 520), "3 · Answer restored locally"),
    (11.2, (360, 560, 1500), "Leak check: passed · 6 values masked"),
]


def scene_app(img, d, t):
    """22-36s: real app footage with zooms."""
    for k in range(len(SHOTS) - 1, -1, -1):
        if t >= SHOTS[k][0]:
            break
    t0, r1, cap = SHOTS[k]
    r0 = SHOTS[k - 1][1] if k else r1
    q = ease_io((t - t0) / 1.0)
    x, y, w = (a + (b - a) * q for a, b in zip(r0, r1))
    h = w * 9 / 16
    x = clamp(x, 0, 1920 - w)
    y = clamp(y, 0, 1080 - h)
    frame = APP.crop((int(x), int(y), int(x + w), int(y + h))).resize((W, H), Image.BILINEAR)
    img.paste(frame, (0, 0))
    d2 = ImageDraw.Draw(img)
    d2.rectangle((0, 0, 380, 64), fill=RED)
    d2.text((28, 8), "REAL APP · LIVE", font=F(BOLD, 36), fill=LIGHTC)
    if cap:
        a = ease((t - t0 - 0.6) / 0.4)
        bar_w = d2.textlength(cap, font=F(BOLD, 60)) + 96
        d2.rounded_rectangle(((W - bar_w) / 2, 900, (W + bar_w) / 2, 1010), 24, fill=mix((255, 255, 255), INK, a))
        d2.text(((W - bar_w) / 2 + 48, 912), cap, font=F(BOLD, 60), fill=mix((255, 255, 255), LIGHTC, a))


def scene_stats(img, d, t):
    """36-45s: the measured result."""
    text_center(d, 120, "Tested on 1,000 Azerbaijani texts it had never seen", F(BOLD, 56), LIGHTC, ease(t / 0.4))
    rows = [("Pərdə", 94.9, RED, 0.6), ("Generic filter", 23.9, MUTED, 1.0)]
    for k, (name, val, col, start) in enumerate(rows):
        y = 330 + k * 230
        p = ease((t - start) / 1.8)
        d.text((180, y), name, font=F(BOLD, 52), fill=LIGHTC)
        d.rounded_rectangle((180, y + 80, 1740, y + 150), 16, fill=PANEL)
        if p > 0:
            d.rounded_rectangle((180, y + 80, 180 + 1560 * val / 100 * p, y + 150), 16, fill=col)
        num = f"{val * p:.1f}%"
        nw = d.textlength(num, font=F(BOLD, 72))
        d.text((1740 - nw, y - 10), num, font=F(BOLD, 72), fill=col if k == 0 else MUTED)
    if t > 3.4:
        a = ease((t - 3.4) / 0.5)
        text_center(d, 820, "of personal data protected", F(LIGHT, 52), MUTED, a)
        text_center(d, 900, "Leak rate: 76.1%  →  5.1%", F(BOLD, 64), AMBER, ease((t - 4.4) / 0.5))


CHIPS = ["FIN 6TR9K2L", "VÖEN", "AZ IBAN", "+994", "AZE / AA ID", "oğlu · qızı", "Rənanın", "Кириллица"]


def scene_az(img, d, t):
    """45-50s: built for Azerbaijan."""
    text_center(d, 140, "Built for Azerbaijani data", F(BOLD, 72), LIGHTC, ease(t / 0.4))
    f = F(MONO, 44)
    x0, y, x = 180, 330, 180
    for k, c in enumerate(CHIPS):
        w = d.textlength(c, font=f) + 72
        if x + w > W - 180:
            x, y = x0, y + 140
        a = ease((t - 0.3 - 0.18 * k) / 0.3)
        if a > 0:
            dy = 30 * (1 - a)
            d.rounded_rectangle((x, y + dy, x + w, y + 100 + dy), 50, fill=mix(INK, PANEL, a), outline=mix(INK, RED, a), width=3)
            d.text((x + 36, y + 22 + dy), c, font=f, fill=mix(INK, LIGHTC, a))
        x += w + 28
    if t > 2.4:
        a = ease((t - 2.4) / 0.5)
        text_center(d, 720, "0.14 ms per message · runs on-premises · no GPU", F(BOLD, 52), AMBER, a)
        text_center(d, 810, "Works with OpenAI · Grok · Gemini · local Ollama", F(LIGHT, 48), MUTED, ease((t - 3.0) / 0.5))


def scene_close(img, d, t):
    """50-56s."""
    if t < 0.9:
        curtain(d, t)
        return
    d.rectangle((0, 0, W, H), fill=INK)
    for k, op in enumerate([1, 0.6, 0.35, 0.15]):
        x = 1340 + k * 60
        d.rectangle((x, 0, x + 28, H), fill=mix(INK, mix(RED, AMBER, 0.3), op))
    d.text((180, 250), "Let the AI read the request.", font=F(BOLD, 88), fill=mix(INK, LIGHTC, ease((t - 1.0) / 0.5)))
    d.text((180, 370), "Never the person.", font=F(BOLD, 88), fill=mix(INK, RED, ease((t - 1.6) / 0.5)))
    a = ease((t - 2.4) / 0.5)
    d.text((180, 600), "Pərdə", font=F(BOLD, 120), fill=mix(INK, LIGHTC, a))
    d.text((186, 770), "Try it: huggingface.co/spaces/Traxic/perde", font=F(REG, 44), fill=mix(INK, MUTED, a))
    d.text((186, 840), "NeuroBridge 2026 · Enterprise track", font=F(REG, 36), fill=mix(INK, MUTED, a))
    if t > DUR - 50.0 - 0.8:
        fade = clamp((t - (DUR - 50.0 - 0.8)) / 0.8)
        img.paste(Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), fade))


SCENES = [
    (0.0, 10.0, scene_hook),
    (10.0, 13.0, scene_question),
    (13.0, 16.0, scene_logo),
    (16.0, 22.0, scene_morph),
    (22.0, 36.0, scene_app),
    (36.0, 45.0, scene_stats),
    (45.0, 50.0, scene_az),
    (50.0, DUR, scene_close),
]
TRANSITIONS = [s for s, _, _ in SCENES[1:]]
HIGHLIGHTS = [5.4 + 0.45 * k for k in range(len(SPANS))]


def frame(t):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    for s, e, fn in SCENES:
        if s <= t < e:
            fn(img, d, t - s)
            # quick fade-in at each scene start
            if t - s < 0.15 and s > 0 and fn not in (scene_logo, scene_close):
                img = Image.blend(Image.new("RGB", (W, H), INK), img, (t - s) / 0.15)
            break
    return img


# --- soundtrack --------------------------------------------------------------

def soundtrack(path):
    sr = 44100
    n = int(DUR * sr)
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    beat = 60 / 118

    def add(sig, at):
        i = int(at * sr)
        j = min(n, i + len(sig))
        if i < n:
            out[i:j] += sig[: j - i]

    tt = np.arange(int(0.25 * sr)) / sr
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    hat_t = np.arange(int(0.04 * sr)) / sr
    hat = rng.normal(0, 1, len(hat_t)) * np.exp(-hat_t * 90)
    hat = np.diff(np.concatenate([[0], hat]))
    bass_notes = [55.0, 55.0, 65.41, 49.0]
    t_cur, k = 0.0, 0
    while t_cur < DUR:
        intro = t_cur < 10.0
        if not intro or k % 2 == 0:
            add(kick * (0.5 if intro else 0.9), t_cur)
        add(hat * 0.12, t_cur + beat / 2)
        if not intro:
            f = bass_notes[(k // 4) % 4]
            bt = np.arange(int(beat * 0.9 * sr)) / sr
            bass = (np.sin(2 * np.pi * f * bt) + 0.3 * np.sin(4 * np.pi * f * bt)) * np.exp(-bt * 3) * 0.35
            add(bass, t_cur)
        t_cur += beat
        k += 1
    # typing clicks while the message types (1.0-4.2s)
    ct = np.arange(int(0.012 * sr)) / sr
    click = rng.normal(0, 1, len(ct)) * np.exp(-ct * 400) * 0.15
    for at in np.arange(1.0, 4.2, 0.045):
        add(click, at)
    # pops on each red highlight
    pt = np.arange(int(0.12 * sr)) / sr
    pop = np.sin(2 * np.pi * 880 * pt) * np.exp(-pt * 30) * 0.35
    for at in HIGHLIGHTS:
        add(pop, at)
    # whooshes on scene changes
    wt = np.arange(int(0.6 * sr)) / sr
    noise = rng.normal(0, 1, len(wt))
    noise = np.convolve(noise, np.ones(30) / 30, mode="same")
    whoosh = noise * np.sin(np.pi * wt / wt[-1]) ** 2 * 0.6
    for at in TRANSITIONS:
        add(whoosh, at - 0.3)
    fade = np.ones(n)
    fl = int(2.0 * sr)
    fade[-fl:] = np.linspace(1, 0, fl)
    out = out * fade
    out = out / max(1e-9, np.abs(out).max()) * 0.8
    pcm = (out * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo.tobytes())


def main():
    wav = HERE / "track.wav"
    soundtrack(wav)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUT)],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    total = int(DUR * FPS)
    for i in range(total):
        proc.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0:
            print(f"frame {i}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 3:  # preview stills: render.py REPO OUT t1 t2 ...
        for ts in sys.argv[3:]:
            frame(float(ts)).save(HERE / f"preview_{ts}.png")
    else:
        main()
