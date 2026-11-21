#!/usr/bin/env python3
"""Rebuild feed.json from rocketry RSS/Atom sources and arXiv.

Runs in GitHub Actions (see .github/workflows/feed.yml). Standard library only.
Hand-written items in feed-manual.json (Hebrew summaries) are always kept on top
of the automatic ones.
"""
import json, re, html, sys, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

RSS = [
    ("SpaceNews", "https://spacenews.com/section/launch/feed/"),
    ("NASASpaceflight", "https://www.nasaspaceflight.com/feed/"),
    ("European Spaceflight", "https://europeanspaceflight.com/feed/"),
    ("Space.com", "https://www.space.com/feeds/launches-spacecraft"),
    ("ESA", "https://www.esa.int/rssfeed/Enabling_Support/Space_Transportation"),
]
ARXIV = [  # (query, category)
    ('all:"hybrid rocket" OR all:"solid rocket motor" OR all:"rocket nozzle"', "academic"),
    ('all:"launch vehicle" AND (all:trajectory OR all:reusable OR all:ascent)', "academic"),
    ('all:"cruise missile" OR all:ramjet OR all:scramjet OR all:"missile guidance"', "missiles"),
]
KEYWORDS = {
    "orbital": r"\b(launch vehicle|launcher|orbit|falcon|starship|electron|neutron|ariane|vega|new glenn|vulcan|h3|pslv|long march|spectrum|rideshare|satellite)\b",
    "launch": r"\b(launch(es|ed)?|liftoff|lift-off|scrub|static fire|hot ?fire)\b",
    "missiles": r"\b(missile|cruise|ramjet|scramjet|hypersonic|interceptor|turbojet)\b",
    "student": r"\b(student|university team|collegiate|irec|spaceport america cup|euroc)\b",
}
UA = {"User-Agent": "TRC-feed-bot/1.0 (+https://github.com)"}
MAX_ITEMS = 60


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def text(s, n=320):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def iso(d):
    if not d:
        return None
    try:
        return parsedate_to_datetime(d).date().isoformat()
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(d.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None


def cats_for(s, default=None):
    s = s.lower()
    cats = [c for c, rx in KEYWORDS.items() if re.search(rx, s)]
    if default and default not in cats:
        cats.insert(0, default)
    return cats


def parse_rss(source, raw):
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for it in root.iter("item"):
        title, link = it.findtext("title"), it.findtext("link")
        desc, date = it.findtext("description"), it.findtext("pubDate")
        out.append((title, link, desc, date))
    for it in root.findall("a:entry", ns):
        link = it.find("a:link", ns)
        out.append((it.findtext("a:title", namespaces=ns), link.get("href") if link is not None else None,
                    it.findtext("a:summary", namespaces=ns), it.findtext("a:updated", namespaces=ns)))
    items = []
    for title, link, desc, date in out:
        if not title or not link:
            continue
        blob = f"{title} {desc or ''}"
        cats = cats_for(blob)
        if not cats:  # keep the feed on-topic
            continue
        items.append({"id": link, "title": text(title, 160), "summary": text(desc), "source": source,
                      "url": link, "date": iso(date), "cats": cats})
    return items


def arxiv(query, cat):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": query, "sortBy": "submittedDate", "sortOrder": "descending", "max_results": 6})
    root = ET.fromstring(fetch(url))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = []
    for e in root.findall("a:entry", ns):
        link = e.findtext("a:id", namespaces=ns)
        title = e.findtext("a:title", namespaces=ns)
        items.append({"id": link, "title": text(title, 160), "summary": text(e.findtext("a:summary", namespaces=ns)),
                      "source": "arXiv", "url": link, "date": iso(e.findtext("a:published", namespaces=ns)),
                      "cats": cats_for(title or "", cat)})
    return items


def main():
    auto = []
    for name, url in RSS:
        try:
            auto += parse_rss(name, fetch(url))
        except Exception as ex:
            print("skip", name, ex, file=sys.stderr)
    for q, c in ARXIV:
        try:
            auto += arxiv(q, c)
        except Exception as ex:
            print("skip arxiv", ex, file=sys.stderr)

    try:
        manual = json.load(open("feed-manual.json", encoding="utf-8"))["items"]
    except FileNotFoundError:
        manual = []

    seen, items = set(), []
    for it in manual + sorted(auto, key=lambda i: i.get("date") or "", reverse=True):
        key = it["url"].split("?")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        items.append(it)
    items = items[:MAX_ITEMS]
    if not items:
        print("no items – keeping old feed.json", file=sys.stderr)
        return
    json.dump({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "items": items},
              open("feed.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"feed.json: {len(items)} items ({len(manual)} manual)")


if __name__ == "__main__":
    main()
