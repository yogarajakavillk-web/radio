import urllib.request, urllib.parse, xml.etree.ElementTree as ET
import json, re, time, os
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
    "User-Agent": "Mozilla/5.0 (compatible; KingFM-RSS-Bot/1.0)",
    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
}

def get_text(el, tag):
    node = el.find(tag)
    if node is None:
        for child in el:
            if child.tag.split("}")[-1] == tag:
                return (child.text or "").strip()
        return ""
    return (node.text or "").strip()

def get_img(item_el, desc_raw):
    enc = item_el.find("enclosure")
    if enc is not None and "image" in enc.get("type",""):
        return enc.get("url","")
    for child in item_el:
        if child.tag.split("}")[-1] in ("content","thumbnail"):
            url = child.get("url","")
            if url.startswith("http"): return url
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_raw, re.I)
    if m and m.group(1).startswith("http"): return m.group(1)
    m = re.search(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp|gif)', desc_raw, re.I)
    return m.group(0) if m else ""

def fetch_feed(feed):
    items = []
    try:
        req = urllib.request.Request(feed["url"], headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        raw_clean = re.sub(r' xmlns[^=]*="[^"]*"', "", raw)
        root = ET.fromstring(raw_clean)
        entries = root.findall(".//item") or root.findall(".//entry")
        for el in entries[:8]:
            title = get_text(el,"title").replace("<![CDATA[","").replace("]]>","").strip()
            if not title or len(title) < 3: continue
            link = get_text(el,"link")
            if not link:
                le = el.find("link")
                if le is not None: link = le.get("href","")
            if not link:
                g = get_text(el,"guid")
                if g.startswith("http"): link = g
            desc_raw = get_text(el,"description") or get_text(el,"summary") or get_text(el,"content")
            body = re.sub(r"<[^>]+>"," ",desc_raw).strip()
            body = re.sub(r"\s+"," ",body)[:500]
            pub = get_text(el,"pubDate") or get_text(el,"published") or get_text(el,"updated")
            img = get_img(el, desc_raw)
            t_lower = (title+" "+body).lower()
            cat_key = "sports" if re.search(r"sport|cricket|football|ipl|விளையாட்டு",t_lower) \
                      else "intl" if re.search(r"world|international|உலக|சர்வதேச",t_lower) \
                      else "local"
            vbase = {"BBC Tamil":8000,"Dinamalar":5000,"Virakesari":3000,
                     "Thinakkural":2000,"OneIndia":4000}.get(feed["name"],1000)
            import random
            views = f"{vbase + random.randint(0, vbase//2):,}"
            items.append({
                "id": abs(hash(link or title)) % 999999999,
                "title": title, "link": link, "body": body, "img": img,
                "time": pub or datetime.now(timezone.utc).isoformat(),
                "source": feed["name"], "views": views,
                "cat": "விளையாட்டு" if cat_key=="sports" else "சர்வதேசம்" if cat_key=="intl" else "செய்திகள்",
                "catKey": cat_key, "status": "publish",
                "_fromRSS": True, "emoji": "📰",
            })
        print(f"✅ {feed['name']}: {len(items)} items")
    except Exception as e:
        print(f"❌ {feed['name']}: {e}")
    return items

all_items = []
for feed in RSS_FEEDS:
    all_items.extend(fetch_feed(feed))
    time.sleep(0.5)

os.makedirs("data", exist_ok=True)
with open("data/news.json","w",encoding="utf-8") as f:
    json.dump({
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(all_items),
        "items": all_items
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(all_items)} items to data/news.json")
```

**4.** **"Commit changes"** → **"Commit changes"**

---

### 📂 Step 4 — data/news.json உருவாக்கவும்

**1.** **"Add file"** → **"Create new file"**

**2.** File name:
```
data/news.json
