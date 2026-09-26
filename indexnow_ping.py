"""Submit every URL in sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver and others share submissions).

Run only after the site has been pushed and GitHub Pages has published it:
    py -3.12 indexnow_ping.py            # submit
    py -3.12 indexnow_ping.py --dry-run  # list what would be sent

Standard library only. The key file https://calcnate.com/<KEY>.txt must be live first.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HOST = "calcnate.com"
KEY = "d011935629dad9143fc3cbe52682655b"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/IndexNow"
ROOT = Path(__file__).resolve().parent


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)
    return [u for u in urls if u.startswith(f"https://{HOST}/")]


def check_key_file():
    local = (ROOT / f"{KEY}.txt").read_text(encoding="utf-8").strip()
    if local != KEY:
        sys.exit(f"Local key file does not contain the key {KEY}")
    try:
        with urllib.request.urlopen(KEY_LOCATION, timeout=20) as r:
            live = r.read().decode("utf-8").strip()
    except urllib.error.URLError as e:
        sys.exit(f"Key file not reachable at {KEY_LOCATION}: {e}. Push and wait for Pages to publish first.")
    if live != KEY:
        sys.exit(f"Live key file at {KEY_LOCATION} does not match the key.")


def submit(urls):
    # IndexNow accepts up to 10,000 URLs per request.
    for start in range(0, len(urls), 10000):
        batch = urls[start:start + 10000]
        payload = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": batch}).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=payload, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                print(f"Submitted {len(batch)} URLs: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"IndexNow returned HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
            return False
    return True


if __name__ == "__main__":
    urls = sitemap_urls()
    if "--dry-run" in sys.argv:
        print("\n".join(urls))
        print(f"{len(urls)} URLs (dry run, nothing sent)")
        sys.exit(0)
    check_key_file()
    sys.exit(0 if submit(urls) else 1)
