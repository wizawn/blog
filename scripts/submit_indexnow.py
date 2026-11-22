#!/usr/bin/env python3
"""Submit canonical sitemap URLs of blog.caowo.de to IndexNow (Bing / ChatGPT Search / Yandex)."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

HOST = "blog.caowo.de"
KEY = "b7e4c9a1d2f84e6093a5c1d7e8f02468"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP_URL = f"https://{HOST}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/IndexNow"


def load_urls(source: str) -> list[str]:
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(source, headers={"User-Agent": "blog-caowo-indexnow/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    else:
        with open(source, "rb") as fh:
            raw = fh.read()
    root = ET.fromstring(raw)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [el.text.strip() for el in root.findall("sm:url/sm:loc", ns) if el.text]


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else SITEMAP_URL
    urls = load_urls(src)
    payload = json.dumps(
        {
            "host": HOST,
            "key": KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": urls,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "blog-caowo-indexnow/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            print(json.dumps({"status": resp.status, "submitted": len(urls), "endpoint": ENDPOINT}))
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": exc.code, "submitted": len(urls), "body": body[:300]}))
        return 0 if exc.code in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
