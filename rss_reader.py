import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import feedparser
import requests

from config import CATEGORY_FEEDS, RSS_CACHE_SECONDS


_CACHE = {"key": None, "at": 0, "items": []}


def extract_image(entry):
    media = entry.get("media_content")
    if isinstance(media, list) and media:
        url = media[0].get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    media_thumb = entry.get("media_thumbnail")
    if isinstance(media_thumb, list) and media_thumb:
        url = media_thumb[0].get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    enclosures = entry.get("enclosures")
    if isinstance(enclosures, list) and enclosures:
        url = enclosures[0].get("href")
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def source_name(feed_url):
    try:
        return urlparse(feed_url).netloc.replace("www.", "") or feed_url
    except Exception:
        return feed_url


def _feeds_for(categories):
    if not categories or "همه" in categories:
        categories = list(CATEGORY_FEEDS.keys())
    seen = set()
    selected = []
    for category in categories:
        for url in CATEGORY_FEEDS.get(category, []):
            if url not in seen:
                seen.add(url)
                selected.append((category, url))
    return selected


def _fetch_one(category, feed_url):
    items = []
    try:
        response = requests.get(feed_url, timeout=8, headers={"User-Agent": "AutoNewsBot/2.1"})
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as error:
        print(f"❌ خطا در خواندن RSS: {feed_url} | {error}")
        return items
    host = source_name(feed_url)
    for entry in feed.entries[:20]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        items.append({"title": title, "link": link, "image": extract_image(entry), "source": feed_url, "source_name": host, "feed_category": category})
    return items


def get_news(categories=None):
    feeds = _feeds_for(categories)
    cache_key = tuple(sorted({url for _, url in feeds}))
    now = time.time()
    if _CACHE["key"] == cache_key and now - _CACHE["at"] < RSS_CACHE_SECONDS:
        return list(_CACHE["items"])
    all_news = []
    seen_links = set()
    if not feeds:
        return []
    workers = min(8, len(feeds))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_fetch_one, category, url) for category, url in feeds]
        for future in as_completed(futures):
            for item in future.result():
                if item["link"] in seen_links:
                    continue
                seen_links.add(item["link"])
                all_news.append(item)
    _CACHE["key"] = cache_key
    _CACHE["at"] = now
    _CACHE["items"] = all_news
    return list(all_news)
