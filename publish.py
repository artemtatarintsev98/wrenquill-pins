#!/usr/bin/env python3
"""Move the next due pins from queue.json into one RSS 2.0 feed per Pinterest board (feeds/<slug>.xml),
with a landing page per published pin (p/<id>.html) as the item link.

Usage: python3 publish.py [--count 3]
Base URL comes from PAGES_URL, else from GITHUB_REPOSITORY (owner/repo) -> https://owner.github.io/repo/.
"""
import datetime, email.utils, html, json, os, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, "queue.json")
FEEDS = os.path.join(ROOT, "feeds")
PAGES = os.path.join(ROOT, "p")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Wren &amp; Quill Studio</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Wren &amp; Quill Studio">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<style>
:root{{--bg:#f6f0e4;--ink:#2e2620;--muted:#6b5d50;--accent:#8a3b2e;--card:#fffaf1;--line:#e3d7c3}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 Georgia,"Times New Roman",serif}}
main{{max-width:640px;margin:0 auto;padding:20px 16px 48px}}
.brand{{font-size:14px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);text-align:center;margin:4px 0 18px}}
.brand a{{color:inherit;text-decoration:none}}
img{{display:block;width:100%;height:auto;border-radius:6px;background:var(--card);box-shadow:0 2px 14px rgba(46,38,32,.12)}}
h1{{font-weight:normal;font-size:clamp(24px,6vw,34px);line-height:1.25;margin:22px 0 12px}}
p.desc{{color:var(--muted);margin:0 0 26px}}
.btn{{display:block;text-align:center;background:var(--accent);color:#fff;text-decoration:none;font-size:20px;padding:17px 20px;border-radius:999px;letter-spacing:.02em}}
.btn:hover,.btn:focus{{background:#6f2f25}}
.note{{text-align:center;font-size:14px;color:var(--muted);margin-top:12px}}
footer{{text-align:center;font-size:14px;color:var(--muted);margin-top:36px;border-top:1px solid var(--line);padding-top:16px}}
footer a{{color:var(--accent)}}
</style>
</head>
<body>
<main>
<div class="brand"><a href="{shop}">Wren &amp; Quill Studio</a></div>
<img src="{img}" alt="{alt}" width="1000" height="1500">
<h1>{title}</h1>
<p class="desc">{desc}</p>
<a class="btn" href="{link}">Shop on Etsy</a>
<p class="note">Instant digital download on Etsy</p>
<footer><a href="{shop}">See the full Wren &amp; Quill shop on Etsy</a></footer>
</main>
</body>
</html>
"""
SHOP = "https://www.etsy.com/shop/WrenAndQuillStudio"


def page_url(p, base):
    return f"{base}p/{p['id']}.html"


def build_page(p, base):
    e = lambda s: html.escape(s, quote=True)
    meta = p["description"] if len(p["description"]) <= 160 else p["description"][:157].rsplit(" ", 1)[0] + "..."
    out = PAGE.format(title=e(p["title"]), meta=e(meta), url=e(page_url(p, base)), img=e(base + p["image"]),
                      alt=e(p.get("alt_text") or p["title"]), desc=e(p["description"]), link=e(p["link"]), shop=SHOP)
    with open(os.path.join(PAGES, p["id"] + ".html"), "w", encoding="utf-8") as f:
        f.write(out)
KEEP = 100
COUNT = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 3


def base_url():
    if os.environ.get("PAGES_URL"):
        return os.environ["PAGES_URL"].rstrip("/") + "/"
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    return f"https://{owner.lower()}.github.io/{repo}/"


def slug(board):
    return "".join(c if c.isalnum() else "-" for c in board.lower().replace("&", "and")).strip("-").replace("--", "-").replace("--", "-")


def build_feed(path, board, published, base):
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = f"Wren & Quill Studio: {board}"
    ET.SubElement(ch, "link").text = "/".join(base.split("/")[:3]) + "/"  # claimed site root
    ET.SubElement(ch, "description").text = "Printable planners, junk journal kits, stickers and clipart by Wren & Quill Studio on Etsy."
    ET.SubElement(ch, "language").text = "en-us"
    ET.SubElement(ch, "lastBuildDate").text = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    for p in published:  # newest first
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, "title").text = p["title"]
        ET.SubElement(it, "link").text = page_url(p, base)
        ET.SubElement(it, "description").text = p["description"]
        ET.SubElement(it, "pubDate").text = email.utils.format_datetime(datetime.datetime.fromisoformat(p["published_at"]))
        ET.SubElement(it, "guid", isPermaLink="true").text = page_url(p, base)
        img = base + p["image"]
        size = os.path.getsize(os.path.join(ROOT, p["image"]))
        ET.SubElement(it, "enclosure", url=img, length=str(size), type="image/jpeg")
    ET.indent(rss)
    ET.ElementTree(rss).write(path, encoding="utf-8", xml_declaration=True)


def main():
    q = json.load(open(QUEUE))
    now = datetime.datetime.now(datetime.timezone.utc)
    pending = sorted((p for p in q if not p.get("published_at")), key=lambda p: p["scheduled_at"])
    due = [p for p in pending if datetime.datetime.fromisoformat(p["scheduled_at"]).replace(tzinfo=datetime.timezone.utc) <= now]
    for i, p in enumerate(due[:COUNT]):
        # a second apart so pubDate order is stable
        p["published_at"] = (now + datetime.timedelta(seconds=i)).isoformat(timespec="seconds")
        print("published", p["id"])
    # Pinterest won't accept an empty feed: seed each board that has nothing yet with its next pin.
    live = {p["board"] for p in q if p.get("published_at")}
    for p in pending:
        if p["board"] not in live:
            live.add(p["board"])
            p["published_at"] = (now - datetime.timedelta(minutes=1)).isoformat(timespec="seconds")
            print("seeded", p["board"], "->", p["id"])
    os.makedirs(FEEDS, exist_ok=True)
    os.makedirs(PAGES, exist_ok=True)
    published = sorted((p for p in q if p.get("published_at")), key=lambda p: p["published_at"], reverse=True)
    for p in published:
        build_page(p, base_url())
    for board in sorted({p["board"] for p in q}):
        items = [p for p in published if p["board"] == board][:KEEP]
        build_feed(os.path.join(FEEDS, slug(board) + ".xml"), board, items, base_url())
    json.dump(q, open(QUEUE, "w"), indent=2, ensure_ascii=False)
    print(f"published total: {len(published)} | due now: {len(due)} | left in queue: {sum(1 for p in q if not p.get('published_at'))}")


if __name__ == "__main__":
    main()
