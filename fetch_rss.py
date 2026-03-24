import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import time
import os
import random
from datetime import datetime, timezone

RSS_FEEDS = [
    {"name": "BBC Tamil",    "url": "https://feeds.bbci.co.uk/tamil/rss.xml"},
    {"name": "Dinamalar",    "url": "https://www.dinamalar.com/rss.asp"},
    {"name": "Virakesari",   "url": "https://www.virakesari.lk/rss.xml"},
    {"name": "Thinakkural",  "url": "https://www.thinakkural.lk/feed/"},
    {"name": "OneIndia",     "url": "https://tamil.oneindia.com/rss/tamil-news.xml"},
    {"name": "jaffnamuslim", "url": "https://www.jaffnamuslim.com/feeds/posts/default?alt=rss"},
    {"name": "news21",       "url": "https://www.news21.lk/rss/category/sri-lanka-tamil-news"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ta,en;q=0.9",
}

VIEW_BASE = {
    "BBC Tamil": 8000, "Dinamalar": 5000, "Virakesari": 3000,
    "Thinakkural": 2000, "OneIndia": 4000, "jaffnamuslim": 1500, "news21": 1000,
}

def get_text(el, tag):
    node = el.find(tag)
    if node is not None:
        return (node.text or "").strip()
    for child in el:
        if child.tag.split("}")[-1] == tag:
            return (child.text or "").strip()
    return ""

def get_img(item_el, desc_raw):
    enc = item_el.find("enclosure")
    if enc is not None and "image" in enc.get("type", ""):
        return enc.get("url", "")
    for child in item_el:
        local = child.tag.split("}")[-1]
        if local in ("content", "thumbnail"):
            u = child.get("url", "")
            if u.startswith("http"):
                return u
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_raw, re.I)
    if m and m.group(1).startswith("http"):
        return m.group(1)
    m = re.search(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp|gif)', desc_raw, re.I)
    return m.group(0) if m else ""

def fetch_feed(feed):
    items = []
    try:
        req = urllib.request.Request(feed["url"], headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        raw_clean = re.sub(r' xmlns[^=]*="[^"]*"', "", raw)
        root = ET.fromstring(raw_clean)
        entries = root.findall(".//item") or root.findall(".//entry")
        for el in entries[:8]:
            title = get_text(el, "title").replace("<![CDATA[", "").replace("]]>", "").strip()
            if not title or len(title) < 3:
                continue
            link = get_text(el, "link")
            if not link:
                link_el = el.find("link")
                if link_el is not None:
                    link = link_el.get("href", "")
            if not link:
                guid = get_text(el, "guid")
                if guid.startswith("http"):
                    link = guid
            desc_raw = (get_text(el, "description") or get_text(el, "summary") or get_text(el, "content"))
            body = re.sub(r"<[^>]+>", " ", desc_raw).strip()
            body = re.sub(r"\s+", " ", body)[:500]
            pub = (get_text(el, "pubDate") or get_text(el, "published") or
                   get_text(el, "updated") or datetime.now(timezone.utc).isoformat())
            img = get_img(el, desc_raw)
            t_lower = (title + " " + body).lower()
            if re.search(r"sport|cricket|football|ipl|விளையாட்டு|கிரிக்கெட்", t_lower):
                cat_key, cat = "sports", "விளையாட்டு"
            elif re.search(r"world|international|global|உலக|சர்வதேச|foreign", t_lower):
                cat_key, cat = "intl", "சர்வதேசம்"
            else:
                cat_key, cat = "local", "செய்திகள்"
            base = VIEW_BASE.get(feed["name"], 1000)
            views = f"{base + random.randint(0, base // 2):,}"
            items.append({
                "id": abs(hash(link or title)) % 999999999,
                "title": title, "link": link, "body": body, "img": img,
                "time": pub, "source": feed["name"], "views": views,
                "cat": cat, "catKey": cat_key, "status": "publish",
                "_fromRSS": True, "emoji": "📰",
            })
        print(f"  OK  {feed['name']}: {len(items)} items")
    except Exception as e:
        print(f"  FAIL {feed['name']}: {e}")
    return items

print("KingFM RSS Fetcher starting...")
all_items = []
for feed in RSS_FEEDS:
    all_items.extend(fetch_feed(feed))
    time.sleep(1)

os.makedirs("data", exist_ok=True)
with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(all_items),
        "items": all_items,
    }, f, ensure_ascii=False, indent=2)

print(f"\nDone: {len(all_items)} items saved to data/news.json")
