#!/usr/bin/env python3
"""Wren & Quill Pinterest pins v2: 5 bold, readable designs per listing + a seasonal 10/day queue.
Usage: python3 make_pins_v2.py SRC_DIR REPO_DIR"""
import os, sys, json, re, random, datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

SRC, REPO = sys.argv[1], sys.argv[2]
W, H = 1000, 1500
F = lambda n, s: ImageFont.truetype(os.path.join(SRC, n), s)
SERIF, SANS = "PlayfairDisplay.ttf", "Quicksand.ttf"

KITS = {  # board, panel colour, text on panel, accent
    "christmas_2026": ("Vintage Christmas Junk Journal & Printables", (122, 30, 32), (251, 243, 228), (216, 180, 106)),
    "winter": ("Vintage Winter Junk Journal & Printables", (35, 52, 74), (247, 242, 233), (190, 214, 228)),
    "cozy": ("Cute Cozy Winter Stickers & Printables", (178, 86, 96), (255, 247, 242), (250, 214, 200)),
    "planner": ("2027 Printable Planners & Calendars", (98, 122, 94), (250, 247, 238), (232, 205, 170)),
    "valentine": ("Valentine's Day Printables & Coquette Crafts", (186, 72, 104), (255, 245, 247), (250, 205, 215)),
    "garden": ("Cottagecore Printables & Garden Junk Journal", (66, 86, 54), (250, 245, 232), (214, 170, 96)),
}
CREAM = (250, 246, 238)
HOOKS = ["INSTANT DOWNLOAD", "PRINT AT HOME", "DIGITAL DOWNLOAD", "PRINTABLE PDF & PNG", "READY TO PRINT"]


def fit(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=(0.5, 0.45))


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines


def text_block(d, text, fontname, maxw, maxh, start=96, minsize=44, spacing=1.12):
    for s in range(start, minsize - 1, -4):
        f = F(fontname, s); ls = wrap(d, text, f, maxw)
        h = int(len(ls) * s * spacing)
        if h <= maxh and len(ls) <= 3: return f, ls, s
    f = F(fontname, minsize); return f, wrap(d, text, f, maxw)[:3], minsize


def draw_center(d, lines, f, size, cx, y, fill, spacing=1.12):
    for l in lines:
        d.text((cx, y), l, font=f, fill=fill, anchor="ma"); y += int(size * spacing)
    return y


def pill(d, cx, y, text, bg, fg, size=30):
    f = F(SANS, size); tw = d.textlength(text, font=f); pw, ph = tw + 64, size + 34
    d.rounded_rectangle((cx - pw / 2, y, cx + pw / 2, y + ph), radius=ph // 2, fill=bg)
    d.text((cx, y + ph / 2), text, font=f, fill=fg, anchor="mm")
    return y + ph


def split_title(t):
    parts = [p.strip() for p in re.split(r"[,|]", t) if p.strip()]
    return parts


def headline(parts, v):
    h = parts[0]
    h = re.sub(r"\b(Printable|PNG|PDF|Instant Download|Digital Download)\b", lambda m: m.group(0), h)
    alt = parts[min(len(parts) - 1, 1 + (v % 2))] if len(parts) > 1 else ""
    return h, alt


def footer(d, y, txt, col):
    d.text((W / 2, y), txt, font=F(SANS, 24), fill=col, anchor="mm")


def v0(imgs, h, sub, k, hook):  # hero top, colour panel bottom
    _, panel, txt, acc = KITS[k]; im = Image.new("RGB", (W, H), panel)
    im.paste(fit(PH(imgs,2), W, 930), (0, 0)); d = ImageDraw.Draw(im)
    y = 980; f, ls, s = text_block(d, h, SERIF, W - 120, 300, 92)
    y = draw_center(d, ls, f, s, W / 2, y, txt); y += 10
    if sub: fs, ls2, s2 = text_block(d, sub.upper(), SANS, W - 140, 90, 34, 24, 1.2); y = draw_center(d, ls2, fs, s2, W / 2, y, acc, 1.2)
    pill(d, W / 2, H - 110, hook, acc, panel, 28); return im


def v1(imgs, h, sub, k, hook):  # cream headline band on top, hero below
    _, panel, txt, acc = KITS[k]; im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im); d.text((W / 2, 52), "WREN & QUILL STUDIO", font=F(SANS, 24), fill=panel, anchor="ma")
    f, ls, s = text_block(d, h, SERIF, W - 110, 280, 96); y = draw_center(d, ls, f, s, W / 2, 100, panel)
    if sub: fs, ls2, s2 = text_block(d, sub, SANS, W - 140, 80, 34, 24, 1.2); y = draw_center(d, ls2, fs, s2, W / 2, y + 6, (110, 98, 86), 1.2)
    top = max(y + 30, 430); im.paste(fit(PH(imgs,1), W, H - top - 90), (0, top))
    d.rectangle((0, H - 90, W, H), fill=panel); footer(d, H - 45, hook + "  ·  SHOP ON ETSY", txt); return im


def v2(imgs, h, sub, k, hook):  # two images + middle band
    _, panel, txt, acc = KITS[k]; im = Image.new("RGB", (W, H), panel)
    a, b = GRID(imgs) or PH(imgs,0), PH(imgs,2)
    im.paste(fit(a, W, 560), (0, 0)); im.paste(fit(b, W, 560), (0, H - 560)); d = ImageDraw.Draw(im)
    f, ls, s = text_block(d, h, SERIF, W - 110, 250, 86, 44)
    tot = len(ls) * int(s * 1.12) + (50 if sub else 0); y = 560 + (380 - tot) // 2
    y = draw_center(d, ls, f, s, W / 2, y, txt)
    if sub: d.text((W / 2, y + 8), (sub.upper())[:44], font=F(SANS, 28), fill=acc, anchor="ma")
    return im


def v3(imgs, h, sub, k, hook):  # full bleed + dark gradient
    _, panel, txt, acc = KITS[k]; im = fit(PH(imgs,1), W, H).convert("RGB")
    grad = Image.new("L", (1, H)); [grad.putpixel((0, y), int(max(0, (y - 700) / 800) ** 1.2 * 235)) for y in range(H)]
    shade = Image.new("RGB", (W, H), (25, 20, 18)); im = Image.composite(shade, im, grad.resize((W, H)))
    d = ImageDraw.Draw(im); f, ls, s = text_block(d, h, SERIF, W - 120, 300, 96)
    tot = len(ls) * int(s * 1.12); y = H - 170 - tot - (54 if sub else 0)
    y = draw_center(d, ls, f, s, W / 2, y, (255, 252, 246))
    if sub: d.text((W / 2, y + 10), sub[:46], font=F(SANS, 32), fill=acc, anchor="ma")
    pill(d, W / 2, H - 120, hook, panel, txt, 28); return im


def v4(imgs, h, sub, k, hook):  # colour bg, framed image, CTA
    _, panel, txt, acc = KITS[k]; im = Image.new("RGB", (W, H), panel); d = ImageDraw.Draw(im)
    f, ls, s = text_block(d, h, SERIF, W - 120, 260, 88); y = draw_center(d, ls, f, s, W / 2, 70, txt)
    pic = fit(GRID(imgs) or PH(imgs,2), 800, 800)
    fr = Image.new("RGB", (836, 836), CREAM); fr.paste(pic, (18, 18))
    sh = Image.new("RGBA", (900, 900), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((32, 40, 868, 876), fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); top = max(y + 40, 360)
    im.paste(sh, (50, top - 30), sh); im.paste(fr, (82, top)); d = ImageDraw.Draw(im)
    y2 = top + 836 + 44
    if sub: d.text((W / 2, y2), sub[:44], font=F(SANS, 32), fill=acc, anchor="ma"); y2 += 60
    pill(d, W / 2, min(y2, H - 110), "SHOP ON ETSY", CREAM, panel, 30); return im


def PH(imgs, i):
    ph = imgs[:3] if len(imgs) >= 4 else imgs[:max(1, len(imgs) - 1)]
    return ph[i % len(ph)]


def GRID(imgs):
    return imgs[3] if len(imgs) >= 5 else None


DESIGNS = [v0, v1, v2, v3, v4]


def pin_text(L, v):
    parts = split_title(L["title"]); tags = [t for t in L["tags"]]
    title = " | ".join([parts[0]] + [parts[(v + i) % (len(parts) - 1) + 1] for i in range(1)] if len(parts) > 1 else [parts[0]])[:100]
    first = (L["desc"].split("\n")[0] or "").strip()
    kw = ", ".join(tags[(v * 3) % max(1, len(tags)):][:5] or tags[:5])
    desc = (f"{first} {parts[0]} — {', '.join(parts[1:4])}. Perfect for {kw}. "
            f"Instant digital download from Wren & Quill Studio on Etsy: print at home or use digitally.")
    return title, re.sub(r"\s+", " ", desc)[:480]


def main():
    man = json.load(open(os.path.join(SRC, "manifest.json")))
    os.makedirs(os.path.join(REPO, "images"), exist_ok=True)
    pins = []
    for L in man:
        if L["status"] != "active" or not L["imgs"]: continue
        imgs = [Image.open(os.path.join(SRC, n)).convert("RGB") for n in L["imgs"]]
        if L["kit"] == "christmas_2026" and len(imgs) >= 4: imgs = imgs[:2] + imgs[3:]  # drop the upsell card
        parts = split_title(L["title"])
        for v, fn in enumerate(DESIGNS):
            h, sub = headline(parts, v); hook = HOOKS[(v + len(L["key"])) % len(HOOKS)]
            pid = f"v2__{L['kit']}__{L['key']}__{v}"; path = f"images/{pid}.jpg"
            fn(imgs, h, sub, L["kit"], hook).convert("RGB").save(os.path.join(REPO, path), quality=88, optimize=True)
            t, desc = pin_text(L, v)
            pins.append(dict(id=pid, image=path, title=t, description=desc, alt_text=L["title"][:490],
                             link=f"https://www.etsy.com/listing/{L['id']}", board=KITS[L["kit"]][0], kit=L["kit"], listing=L["id"], v=v))
    return pins


def weights(day):
    if day < datetime.date(2026, 12, 16):
        return {"christmas_2026": 3, "winter": 2, "cozy": 2, "planner": 2, "valentine": 1, "garden": 0.6}
    if day < datetime.date(2026, 12, 24):
        return {"christmas_2026": 0.6, "winter": 2, "cozy": 1.5, "planner": 3, "valentine": 2.5, "garden": 0.8}
    return {"christmas_2026": 0, "winter": 1.2, "cozy": 0.8, "planner": 2.5, "valentine": 3.5, "garden": 1.5}


def schedule(pins, start, per_day=10, hours=(14, 15, 16, 17, 18, 19, 20, 21, 22, 23)):
    pools = {}
    for p in sorted(pins, key=lambda p: (p["v"], random.Random(p["listing"]).random())):
        pools.setdefault(p["kit"], []).append(p)
    credit = {k: 0.0 for k in pools}; out = []; day = start
    while any(pools.values()) and day < start + datetime.timedelta(days=120):
        w = weights(day); used = set(); n = 0
        for _ in range(per_day * 6):
            if n >= per_day: break
            for k in credit: credit[k] += w.get(k, 0) if pools.get(k) else 0
            k = max((k for k in pools if pools[k] and w.get(k, 0) > 0), key=lambda k: credit[k], default=None)
            if not k: break
            p = next((x for x in pools[k] if x["listing"] not in used), None)
            credit[k] -= sum(w.values())
            if not p: continue
            pools[k].remove(p); used.add(p["listing"])
            p["scheduled_at"] = datetime.datetime.combine(day, datetime.time(6, 0, n)).isoformat()
            out.append(p); n += 1
        day += datetime.timedelta(days=1)
    return out


if __name__ == "__main__":
    pins = main()
    q = json.load(open(os.path.join(REPO, "queue.json")))
    keep = [p for p in q if p.get("published_at") or p["id"].startswith("christmas_2026__main")]
    sched = schedule(pins, datetime.date(2026, 11, 20))
    for p in sched:
        for x in ("kit", "listing", "v"): p.pop(x)
    for p in keep:
        if p["id"].startswith("christmas_2026__main") and not p.get("published_at"):
            p["scheduled_at"] = min(p["scheduled_at"], "2026-12-10T09:00:00")
    new = keep + sched
    json.dump(new, open(os.path.join(REPO, "queue.json"), "w"), indent=2, ensure_ascii=False)
    import collections
    print("pins", len(pins), "scheduled", len(sched), "kept", len(keep), "last", sched[-1]["scheduled_at"] if sched else None)
    print(collections.Counter(p["board"] for p in sched))
