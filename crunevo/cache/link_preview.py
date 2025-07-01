import os
import json
import time
import logging
import re
from urllib.parse import urlparse

import redis
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

KEY_PREFIX = "link_preview:"
TTL = 6 * 60 * 60  # 6 hours

_fallback = {}

URL_REGEX = r"(https?://[^\s]+)"


def _client():
    from redis.exceptions import RedisError

    try:
        r.ping()
        return r
    except RedisError as exc:  # pragma: no cover - fakeredis won't hit
        log.warning("Redis ping failed – using memory cache: %s", exc)
        return None


def extract_first_url(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(URL_REGEX, text)
    return m.group(0) if m else None


def _fetch(url: str) -> dict | None:
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        def meta(prop):
            tag = soup.find("meta", property=prop) or soup.find(
                "meta", attrs={"name": prop}
            )
            return tag["content"].strip() if tag and tag.get("content") else None

        description = meta("og:description") or meta("description")
        image = meta("og:image")
        site_name = meta("og:site_name") or urlparse(url).netloc
        return {
            "url": url,
            "title": title,
            "description": description,
            "image": image,
            "site_name": site_name,
        }
    except Exception as exc:  # pragma: no cover
        log.warning("preview fetch failed for %s: %s", url, exc)
        return None


def get_preview(url: str) -> dict | None:
    cli = _client()
    key = KEY_PREFIX + url
    if cli:
        try:
            cached = cli.get(key)
            if cached:
                return json.loads(cached)
        except redis.RedisError:
            pass
    now = time.time()
    entry = _fallback.get(url)
    if entry and entry[1] > now:
        return entry[0]

    data = _fetch(url)
    if data:
        if cli:
            try:
                cli.setex(key, TTL, json.dumps(data))
            except redis.RedisError:
                pass
        _fallback[url] = (data, now + TTL)
    return data
