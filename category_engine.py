# ==========================
# Category Engine v2.0
# ==========================

from urllib.parse import urlparse

from config import CATEGORY_RULES


def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = text.strip().lower()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("‌", " ")
    text = " ".join(text.split())
    return text


def source_host(source):
    if not isinstance(source, str):
        return ""

    source = source.strip().lower()
    if not source:
        return ""

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
            score -= 4

    for site in rules.get("sources", []):
        site = normalize_text(site)
        if site and (site in host or site in raw_source):
            score += 12

    return score


def detect_category_scores(title, source=""):
    scores = {}
    for category, rules in CATEGORY_RULES.items():
        scores[category] = score_category(title, source, rules)
    return scores


def detect_categories(title, source=""):
    scores = detect_category_scores(title, source)
    matched = [name for name, value in scores.items() if value >= 3]

    if matched:
        return matched

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return [best]

    return []


def detect_category_advanced(title, source=""):
    matched = detect_categories(title, source)
    if not matched:
        return "عمومی"
    scores = detect_category_scores(title, source)
    return max(matched, key=lambda name: scores.get(name, 0))


def news_matches_channel(title, source, selected_categories):
    if not selected_categories:
        return False

    if "همه" in selected_categories:
        return True

    detected = detect_categories(title, source)
    return any(item in selected_categories for item in detected)
