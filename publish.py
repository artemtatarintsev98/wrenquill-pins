#!/usr/bin/env python3
"""Move the next due pins from queue.json into one RSS 2.0 feed per Pinterest board (feeds/<slug>.xml).

Usage: python3 publish.py [--count 3]
Base URL comes from PAGES_URL, else from GITHUB_REPOSITORY (owner/repo) -> https://owner.github.io/repo/.
"""
import datetime, email.utils, json, os, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, "queue.json")
FEEDS = os.path.join(ROOT, "feeds")
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
    ET.SubElement(ch, "link").text = base
    ET.SubElement(ch, "description").text = "Printable planners, junk journal kits, stickers and clipart by Wren & Quill Studio on Etsy."
    ET.SubElement(ch, "language").text = "en-us"
    ET.SubElement(ch, "lastBuildDate").text = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    for p in published:  # newest first
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, "title").text = p["title"]
        ET.SubElement(it, "link").text = p["link"]
        ET.SubElement(it, "description").text = p["description"]
        ET.SubElement(it, "pubDate").text = email.utils.format_datetime(datetime.datetime.fromisoformat(p["published_at"]))
        ET.SubElement(it, "guid", isPermaLink="false").text = p["id"]
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
    published = sorted((p for p in q if p.get("published_at")), key=lambda p: p["published_at"], reverse=True)
    for board in sorted({p["board"] for p in q}):
        items = [p for p in published if p["board"] == board][:KEEP]
        build_feed(os.path.join(FEEDS, slug(board) + ".xml"), board, items, base_url())
    json.dump(q, open(QUEUE, "w"), indent=2, ensure_ascii=False)
    print(f"published total: {len(published)} | due now: {len(due)} | left in queue: {sum(1 for p in q if not p.get('published_at'))}")


if __name__ == "__main__":
    main()
