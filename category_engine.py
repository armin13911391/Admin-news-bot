from urllib.parse import urlparse

from config import CATEGORY_RULES, IRAN_HINTS


def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = text.replace("ي", "ی").replace("ك", "ک").replace("‌", " ")
    return " ".join(text.split())


def source_host(source):
    if not isinstance(source, str):
        return ""
    source = source.strip().lower()
    if "://" not in source:
        return source
    try:
        return urlparse(source).netloc.replace("www.", "")
    except Exception:
        return source


def score_category(title, source, rules):
    text = normalize_text(title)
    host = source_host(source)
    raw_source = normalize_text(source)
    score = 0
    for word in rules.get("keywords", []):
        word = normalize_text(word)
        if word and word in text:
            score += 3
    for word in rules.get("negative", []):
        word = normalize_text(word)
        if word and word in text:
            score -= 5
    for site in rules.get("sources", []):
        site = normalize_text(site)
        if site and (site in host or site in raw_source):
            score += 12
    return score


def _is_valid_for_category(title, source, category, feed_category=None):
    rules = CATEGORY_RULES.get(category, {})
    text = normalize_text(title)
    raw = normalize_text(source) + " " + text
    if rules.get("require_iran"):
        has_hint = any(normalize_text(word) in text for word in IRAN_HINTS)
        iranian_source = any(site in raw for site in ("isna", "irna", "irimo", "mehrnews"))
        if not has_hint and not iranian_source:
            return False
    if category == "آب‌وهوا":
        weather_words = [normalize_text(w) for w in rules.get("keywords", [])]
        if any(word and word in text for word in weather_words):
            return True
        return feed_category == "آب‌وهوا" and any(
            word in text for word in ("هوا", "باران", "برف", "آلودگی", "دما")
        )
    return True


def detect_categories(title, source="", feed_category=None):
    if feed_category and feed_category in CATEGORY_RULES:
        if _is_valid_for_category(title, source, feed_category, feed_category):
            return [feed_category]
    scores = {name: score_category(title, source, rules) for name, rules in CATEGORY_RULES.items()}
    matched = [name for name, value in scores.items() if value >= 3 and _is_valid_for_category(title, source, name, feed_category)]
    if matched:
        return matched
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0 and _is_valid_for_category(title, source, best, feed_category):
            return [best]
    return []


def detect_category_advanced(title, source="", feed_category=None):
    matched = detect_categories(title, source, feed_category)
    return matched[0] if matched else "عمومی"


def news_matches_channel(title, source, selected_categories, feed_category=None):
    if not selected_categories:
        return False
    if "همه" in selected_categories:
        return True
    detected = detect_categories(title, source, feed_category)
    return any(item in selected_categories for item in detected)
