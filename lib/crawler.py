#!/usr/bin/env python3
"""
crawl_and_cors.py
—————————————————————————————————————————————————————————
Crawl  https://my.hiredly.com/about-us
Find   every URL that points to cms.hiredly.com
Check  whether each one returns Access-Control-Allow-Origin
       for requests coming from https://my.hiredly.com

Exit status:
    0  all cms URLs allow CORS  ➜  PASS
    1  at least one blocks it   ➜  FAIL
"""

import re, sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ─────────────── configuration ───────────────
PAGE_URL   = "https://my.hiredly.com/about-us"
ORIGIN     = "https://my.hiredly.com"
TARGET_NET = "cms.hiredly.com"
TIMEOUT    = 15     # seconds
# ──────────────────────────────────────────────


def extract_cms_urls(html: str, base: str) -> set[str]:
    """Return every unique cms.hiredly.com URL found in tags or inline JS."""
    soup  = BeautifulSoup(html, "html.parser")
    urls  = set()

    # 1) src/href/data-* attributes
    for tag in soup.find_all(True):
        for attr in ("src", "href", "data-src", "data-href"):
            if tag.has_attr(attr):
                full = urljoin(base, tag[attr])
                if TARGET_NET in urlparse(full).netloc:
                    urls.add(full)

    # 2) inline <script> bodies
    for script in soup.find_all("script"):
        if script.string:
            for m in re.findall(r"https?://[^\s\"'<>]+", script.string):
                if TARGET_NET in urlparse(m).netloc:
                    urls.add(m)

    return urls


def cors_ok(url: str, origin: str) -> bool:
    """True if url’s response includes ACAO = {origin|*} (OPTIONS or GET)."""
    hdr = {"Origin": origin}

    try:
        opt = requests.options(
            url,
            headers={
                **hdr,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=TIMEOUT,
        )
        allow = opt.headers.get("Access-Control-Allow-Origin")

        # Fallback: some servers don’t answer OPTIONS
        if allow is None:
            get  = requests.get(url, headers=hdr, timeout=TIMEOUT)
            allow = get.headers.get("Access-Control-Allow-Origin")

        return allow in {origin, "*"}
    except requests.RequestException as e:
        print(f"[error] {url} → {e}")
        return False


def main() -> None:
    try:
        resp = requests.get(PAGE_URL, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Cannot fetch {PAGE_URL}: {e}")
        sys.exit(1)

    cms_links = extract_cms_urls(resp.text, PAGE_URL)

    if not cms_links:
        print("No cms.hiredly.com references found – PASS")
        sys.exit(0)

    print(f"Found {len(cms_links)} cms.hiredly.com URL(s) on the page\n")

    all_ok = True
    for link in sorted(cms_links):
        ok = cors_ok(link, ORIGIN)
        print(f"{'PASS' if ok else 'FAIL'}  {link}")
        all_ok &= ok

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
