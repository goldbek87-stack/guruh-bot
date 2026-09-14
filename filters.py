"""
Xabar ichidan link topish va uni taqiqlangan domenlar ro'yxati bilan
solishtirish mantig'i. Yangi turdagi qoida (masalan "faqat rasm bilan
e'lon qabul qilinsin" kabi) qo'shmoqchi bo'lsangiz, shu faylga yangi
funksiya qo'shib, handlers.py da chaqirishingiz mumkin.
"""

import re
from urllib.parse import urlparse

from config import BLOCKED_DOMAINS, OWN_GROUP_USERNAME

URL_REGEX = re.compile(
    r"(?:https?://|www\.)[^\s]+|(?:t\.me|telegram\.me)/[^\s]+",
    re.IGNORECASE,
)


def _extract_from_entities(message):
    urls = []
    text = message.text or message.caption or ""
    entities = list(message.entities or []) + list(message.caption_entities or [])
    for ent in entities:
        if ent.type == "url":
            urls.append(text[ent.offset: ent.offset + ent.length])
        elif ent.type == "text_link" and ent.url:
            urls.append(ent.url)
    return urls


def extract_urls(message):
    urls = set(_extract_from_entities(message))
    text = message.text or message.caption or ""
    urls.update(URL_REGEX.findall(text))
    return list(urls)


def _normalize(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


def _domain_of(url):
    try:
        netloc = urlparse(_normalize(url)).netloc.lower()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _path_of(url):
    try:
        return urlparse(_normalize(url)).path.lstrip("/").lower()
    except Exception:
        return ""


def find_blocked_link(message):
    """Xabardagi linklarni tekshiradi.
    Taqiqlangan domen topilsa - o'sha linkni qaytaradi, aks holda None."""
    for url in extract_urls(message):
        domain = _domain_of(url)
        if not domain:
            continue

        # O'z guruh linki bo'lsa - bloklanmaydi
        if domain in ("t.me", "telegram.me") and OWN_GROUP_USERNAME:
            path = _path_of(url)
            if path.startswith(OWN_GROUP_USERNAME.lower()):
                continue

        for blocked in BLOCKED_DOMAINS:
            if domain == blocked or domain.endswith("." + blocked):
                return url
    return None
