import feedparser
from urllib.parse import urlparse

from config import RSS_FEEDS


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
        host = urlparse(feed_url).netloc.replace("www.", "")
        return host or feed_url
    except Exception:
        return feed_url


def get_news():
    all_news = []
    seen_links = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            host = source_name(feed_url)

            for entry in feed.entries:
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()

                if not title or not link or link in seen_links:
                    continue

                seen_links.add(link)
                all_news.append({
                    "title": title,
                    "link": link,
                    "image": extract_image(entry),
                    "source": feed_url,
                    "source_name": host,
                })

        except Exception as error:
            print(f"❌ خطا در خواندن RSS: {feed_url}")
            print(error)

    return all_news
