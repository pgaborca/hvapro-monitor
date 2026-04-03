#!/usr/bin/env python3
"""
Hardverapro listing monitor
Checks for new iPhone 16 Pro "keresett" listings every 60 minutes
and sends an email notification via Resend when new ones appear.

Configuration: set environment variables (see .env.example)
"""

import time
import json
import hashlib
import logging
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
#  CONFIG  –  from environment variables
# ─────────────────────────────────────────────
CONFIG = {
    "url": (
        "https://hardverapro.hu/aprok/mobil/mobil/iphone/iphone_16/iphone_16_pro/keres.php"
        "?stext=&stcid_text=&stcid=&stmid_text=&stmid="
        "&minprice=210000&maxprice=250000"
        "&cmpid_text=&cmpid=&usrid_text=&usrid="
        "&__buying=1&__buying=0&stext_none=&__brandnew=1&__brandnew=0"
    ),
    "interval_seconds": int(os.environ.get("INTERVAL_SECONDS", 3600)),
    "resend_api_key":   os.environ.get("RESEND_API_KEY", ""),
    "email_from":       os.environ.get("EMAIL_FROM", ""),   # e.g. alerts@yourdomain.com
    "email_to":         os.environ.get("EMAIL_TO", ""),
    # State file lives in /app/data – persisted via Docker volume
    "state_file":       "/app/data/hardverapro_seen.json",
}
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
}


# ── State helpers ────────────────────────────────────────────────────────────

def load_seen() -> set:
    path = Path(CONFIG["state_file"])
    if path.exists():
        try:
            return set(json.loads(path.read_text()))
        except Exception:
            pass
    return set()


def save_seen(seen: set):
    Path(CONFIG["state_file"]).write_text(json.dumps(list(seen)))


# ── Scraping ─────────────────────────────────────────────────────────────────

def fetch_listings() -> list[dict]:
    try:
        resp = requests.get(CONFIG["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("Failed to fetch page: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    listings = []

    for item in soup.select("ul.media-list li"):
        link_tag = item.select_one("a.uad-title")
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)

        if href.startswith("/"):
            href = "https://hardverapro.hu" + href

        listing_id = _extract_id(href)

        price_tag = item.select_one(".uad-price")
        price = price_tag.get_text(strip=True) if price_tag else "?"

        date_tag = item.select_one(".uad-cdate, time")
        date = date_tag.get_text(strip=True) if date_tag else ""

        listings.append({
            "id": listing_id,
            "title": title,
            "price": price,
            "url": href,
            "date": date,
        })

    return listings


def _extract_id(url: str) -> str:
    m = re.search(r"/(\d{6,})", url)
    if m:
        return m.group(1)
    return hashlib.md5(url.encode()).hexdigest()[:12]


# ── Email via Resend ──────────────────────────────────────────────────────────

def send_email(new_listings: list[dict]):
    count = len(new_listings)
    subject = f"[Hardverapro] {count} új hirdetés – iPhone 16 Pro keresett"

    rows_html = ""
    rows_text = ""
    for l in new_listings:
        rows_html += (
            f'<tr>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;">'
            f'<a href="{l["url"]}" style="color:#d63031;text-decoration:none;font-weight:500;">'
            f'{l["title"]}</a>'
            f'</td>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;white-space:nowrap;font-weight:600;">'
            f'{l["price"]}'
            f'</td>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;color:#999;font-size:12px;">'
            f'{l["date"]}'
            f'</td>'
            f'</tr>\n'
        )
        rows_text += f"• {l['title']} — {l['price']}\n  {l['url']}\n\n"

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9f9f9;font-family:Arial,sans-serif;">
  <div style="max-width:640px;margin:32px auto;background:#fff;border-radius:8px;
              box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;">
    <div style="background:#d63031;padding:20px 28px;">
      <h2 style="margin:0;color:#fff;font-size:20px;">
        📱 {count} új hirdetés – Hardverapro
      </h2>
      <p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:13px;">
        iPhone 16 Pro • keresett • 210 000 – 250 000 Ft
      </p>
    </div>
    <div style="padding:24px 28px;">
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f5f5f5;">
            <th style="padding:8px 14px;text-align:left;font-weight:600;color:#555;">Hirdetés</th>
            <th style="padding:8px 14px;text-align:left;font-weight:600;color:#555;">Ár</th>
            <th style="padding:8px 14px;text-align:left;font-weight:600;color:#555;">Dátum</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
      <div style="margin-top:24px;">
        <a href="{CONFIG['url']}"
           style="display:inline-block;background:#d63031;color:#fff;text-decoration:none;
                  padding:10px 20px;border-radius:5px;font-size:14px;font-weight:600;">
          ➜ Összes találat megtekintése
        </a>
      </div>
    </div>
    <div style="padding:14px 28px;background:#f5f5f5;font-size:11px;color:#bbb;">
      Automatikus értesítő – hardverapro_monitor
    </div>
  </div>
</body>
</html>
"""

    text_body = (
        f"Új Hardverapro hirdetések – iPhone 16 Pro keresett (210k–250k Ft)\n\n"
        f"{rows_text}\n{CONFIG['url']}"
    )

    payload = {
        "from": CONFIG["email_from"],
        "to": [CONFIG["email_to"]],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {CONFIG['resend_api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        email_id = resp.json().get("id", "?")
        log.info("Email sent via Resend (id=%s): %d new listing(s)", email_id, count)
    except requests.RequestException as e:
        log.error("Failed to send email via Resend: %s", e)
        if hasattr(e, "response") and e.response is not None:
            log.error("Resend response: %s", e.response.text)


# ── Main loop ─────────────────────────────────────────────────────────────────

def check_once(seen: set) -> set:
    log.info("Fetching listings…")
    listings = fetch_listings()

    if not listings:
        log.warning("No listings parsed (page structure may have changed or fetch failed).")
        return seen

    log.info("Found %d listing(s) on page.", len(listings))

    new_ones = [l for l in listings if l["id"] not in seen]

    if new_ones:
        log.info("%d NEW listing(s) found – sending email.", len(new_ones))
        send_email(new_ones)
        for l in new_ones:
            log.info("  + %s | %s | %s", l["id"], l["price"], l["title"][:60])
    else:
        log.info("No new listings.")

    for l in listings:
        seen.add(l["id"])

    return seen


def main():
    Path(CONFIG["state_file"]).parent.mkdir(parents=True, exist_ok=True)

    missing = [k for k in ("resend_api_key", "email_from", "email_to") if not CONFIG[k]]
    if missing:
        log.error("Missing required env var(s): %s", ", ".join(k.upper() for k in missing))
        raise SystemExit(1)

    log.info("Hardverapro monitor started. Interval: %ds", CONFIG["interval_seconds"])
    seen = load_seen()
    log.info("Loaded %d previously seen listing ID(s).", len(seen))

    while True:
        try:
            seen = check_once(seen)
            save_seen(seen)
        except Exception as e:
            log.exception("Unexpected error during check: %s", e)

        log.info("Next check in %d minutes.", CONFIG["interval_seconds"] // 60)
        time.sleep(CONFIG["interval_seconds"])


if __name__ == "__main__":
    main()
