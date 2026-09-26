# ==========================
# AutoNewsBot Config v2.0
# ==========================

import os

# توکن را در متغیر محیطی BALE_BOT_TOKEN بگذار.
# مقدار زیر فقط برای سازگاری با نسخه فعلی است؛ ریپوی عمومی توکن را لو می‌دهد.
BOT_TOKEN = os.getenv(
    "BALE_BOT_TOKEN",
    "1159197217:ZwrWy4kXoTdu7hSMHMWjjaQKm-uM1qlUCYs",
)

USERS_FILE = "data/users.json"
SENT_NEWS_FILE = "data/sent_news.json"

MAX_SENT_NEWS = 5000
CHECK_EMPTY_INTERVAL = 60
SEND_INTERVALS = [300, 600]
MAX_CHANNELS = 3

RSS_FEEDS = [
    "https://www.tasnimnews.com/fa/rss/feed/0/7/0",
    "https://www.mehrnews.com/rss",
    "https://www.isna.ir/rss",
    "https://www.irna.ir/rss",
    "https://www.farsnews.ir/rss",
    "https://www.yjc.ir/fa/rss",
    "https://www.ilna.ir/rss",
    "https://www.iribnews.ir/fa/rss",
    "https://defapress.ir/fa/rss",
    "https://nournews.ir/fa/rss",
    "https://www.eghtesadnews.com/rss",
    "https://www.tgju.org/rss",
    "https://www.varzesh3.com/rss",
    "https://www.khabarvarzeshi.com/rss",
    "https://www.zoomit.ir/feed/",
    "https://www.irna.ir/rss/tp/32",
]


CATEGORY_RULES = {
    "ورزش": {
        "sources": ["varzesh3", "khabarvarzeshi"],
        "keywords": [
            "فوتبال", "والیبال", "بسکتبال", "لیگ برتر", "لیگ",
            "جام جهانی", "بازیکن", "مربی", "مسابقه", "قهرمانی",
            "استقلال", "پرسپولیس", "ورزش", "گل زد", "داور", "تیم ملی",
        ],
        "negative": ["جنگ", "حمله نظامی", "موشک", "ارتش", "هواشناسی", "بارش"],
    },
    "اقتصاد": {
        "sources": ["tgju", "eghtesadnews"],
        "keywords": [
            "دلار", "طلا", "سکه", "بورس", "ارز", "اقتصاد", "بازار",
            "تورم", "نرخ ارز", "بانک مرکزی", "نفت",
        ],
        "negative": ["فوتبال", "مسابقه ورزشی", "جنگنده", "هواشناسی"],
    },
    "جنگ": {
        "sources": ["defapress", "nournews"],
        "keywords": [
            "حمله نظامی", "حمله موشکی", "موشک", "پهپاد", "ارتش",
            "نیروی نظامی", "عملیات نظامی", "درگیری مسلحانه",
            "جنگنده", "تجاوز نظامی", "شهادت", "بمباران", "جبهه جنگ",
        ],
        "negative": ["آتش سوزی جنگل", "جنگل", "ورزش", "مسابقه", "هواشناسی", "بارش"],
    },
    "فناوری": {
        "sources": ["zoomit"],
        "keywords": [
            "گوشی", "موبایل", "لپ تاپ", "هوش مصنوعی", "تکنولوژی",
            "اینترنت", "نرم افزار", "اپلیکیشن", "استارتاپ",
        ],
        "negative": ["جنگ", "موشک", "فوتبال"],
    },
    "سیاسی": {
        "sources": [],
        "keywords": [
            "مجلس", "دولت", "وزیر", "هیئت دولت", "رئیس جمهور",
            "رئیس‌جمهور", "انتخابات", "نماینده مجلس",
            "سیاست خارجی", "مذاکره", "مصوبه", "لایحه",
        ],
        "negative": ["فوتبال", "هواشناسی", "موشک"],
    },
    "آب‌وهوا": {
        "sources": ["irimo", "weather"],
        "keywords": [
            "هواشناسی", "پیش بینی هوا", "پیش‌بینی هوا", "وضعیت هوا",
            "بارش باران", "بارش برف", "سامانه بارشی", "هشدار هواشناسی",
            "هشدار زرد", "هشدار نارنجی", "هشدار قرمز", "وزش باد شدید",
            "کاهش دما", "افزایش دما", "گرد و غبار", "آلودگی هوا",
            "رگبار", "تگرگ", "طوفان", "سیلاب",
        ],
        "negative": ["موشک", "پهپاد", "فوتبال", "دلار", "بورس"],
    },
}

FORCE_JOIN_ENABLED = True

FORCE_JOIN_CHANNELS = [
    {
        "id": 5156805259,
        "username": "@adminbots_ir",
    }
]
