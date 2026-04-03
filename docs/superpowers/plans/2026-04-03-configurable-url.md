# Configurable Search URL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded Hardverapro search URL with a required `MONITOR_URL` environment variable and generalize hardcoded email copy.

**Architecture:** All changes are confined to `hardverapro_monitor.py`, `env.example`, and `docker-compose.yml`. The URL moves from a hardcoded string in `CONFIG` to an env var loaded the same way as `RESEND_API_KEY`. Email copy that referenced "iPhone 16 Pro" is replaced with generic strings.

**Tech Stack:** Python 3, python-dotenv (implicit via Docker), BeautifulSoup4, Requests

---

### Task 1: Add MONITOR_URL env var to CONFIG and required-vars check

**Files:**
- Modify: `hardverapro_monitor.py:24-38` (CONFIG dict)
- Modify: `hardverapro_monitor.py:255-258` (required vars check in `main()`)

- [ ] **Step 1: Replace the hardcoded URL in CONFIG**

In `hardverapro_monitor.py`, replace lines 24–38:

```python
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
    "email_from":       os.environ.get("EMAIL_FROM", ""),
    "email_to":         os.environ.get("EMAIL_TO", ""),
    "state_file":       "/app/data/hardverapro_seen.json",
}
```

with:

```python
CONFIG = {
    "url":              os.environ.get("MONITOR_URL", ""),
    "interval_seconds": int(os.environ.get("INTERVAL_SECONDS", 3600)),
    "resend_api_key":   os.environ.get("RESEND_API_KEY", ""),
    "email_from":       os.environ.get("EMAIL_FROM", ""),
    "email_to":         os.environ.get("EMAIL_TO", ""),
    "state_file":       "/app/data/hardverapro_seen.json",
}
```

- [ ] **Step 2: Add MONITOR_URL to the required-vars check in main()**

In `hardverapro_monitor.py`, replace:

```python
    missing = [k for k in ("resend_api_key", "email_from", "email_to") if not CONFIG[k]]
```

with:

```python
    missing = [k for k in ("url", "resend_api_key", "email_from", "email_to") if not CONFIG[k]]
```

Also update the error log message key display. The current line prints the key name directly — `"url"` would show as `URL` which is confusing. Replace that line entirely:

```python
    if missing:
        key_map = {"url": "MONITOR_URL", "resend_api_key": "RESEND_API_KEY",
                   "email_from": "EMAIL_FROM", "email_to": "EMAIL_TO"}
        log.error("Missing required env var(s): %s", ", ".join(key_map[k] for k in missing))
        raise SystemExit(1)
```

- [ ] **Step 3: Verify the app exits with a clear error when MONITOR_URL is unset**

Run (with MONITOR_URL absent, other vars set to dummy values):

```bash
RESEND_API_KEY=x EMAIL_FROM=a@b.com EMAIL_TO=c@d.com python hardverapro_monitor.py
```

Expected output contains:
```
ERROR    Missing required env var(s): MONITOR_URL
```
and the process exits with code 1.

- [ ] **Step 4: Commit**

```bash
git add hardverapro_monitor.py
git commit -m "feat: replace hardcoded URL with required MONITOR_URL env var"
```

---

### Task 2: Generalize hardcoded email copy

**Files:**
- Modify: `hardverapro_monitor.py:127-195` (`send_email()` function)

- [ ] **Step 1: Replace the hardcoded email subject**

In `send_email()`, replace:

```python
    subject = f"[Hardverapro] {count} új hirdetés – iPhone 16 Pro keresett"
```

with:

```python
    subject = f"[Hardverapro] {count} új hirdetés"
```

- [ ] **Step 2: Replace the hardcoded HTML subtitle**

In `send_email()`, replace:

```python
      <p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:13px;">
        iPhone 16 Pro • keresett • 210 000 – 250 000 Ft
      </p>
```

with:

```python
      <p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:13px;word-break:break-all;">
        {CONFIG['url']}
      </p>
```

- [ ] **Step 3: Replace the hardcoded plain-text preamble**

In `send_email()`, replace:

```python
        f"Új Hardverapro hirdetések – iPhone 16 Pro keresett (210k–250k Ft)\n\n"
```

with:

```python
        f"Új Hardverapro hirdetések\n\n"
```

- [ ] **Step 4: Verify the change manually**

Run a quick syntax check:

```bash
python -m py_compile hardverapro_monitor.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add hardverapro_monitor.py
git commit -m "feat: generalize hardcoded iPhone email copy to generic strings"
```

---

### Task 3: Update config files

**Files:**
- Modify: `env.example`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add MONITOR_URL to env.example**

Add this line to `env.example` (before `INTERVAL_SECONDS`):

```
MONITOR_URL=https://hardverapro.hu/aprok/mobil/mobil/iphone/iphone_16/iphone_16_pro/keres.php?stext=&stcid_text=&stcid=&stmid_text=&stmid=&minprice=210000&maxprice=250000&cmpid_text=&cmpid=&usrid_text=&usrid=&__buying=1&__buying=0&stext_none=&__brandnew=1&__brandnew=0
```

The full `env.example` should look like:

```
RESEND_API_KEY=your_resend_api_key_here
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=you@example.com
MONITOR_URL=https://hardverapro.hu/aprok/mobil/mobil/iphone/iphone_16/iphone_16_pro/keres.php?stext=&stcid_text=&stcid=&stmid_text=&stmid=&minprice=210000&maxprice=250000&cmpid_text=&cmpid=&usrid_text=&usrid=&__buying=1&__buying=0&stext_none=&__brandnew=1&__brandnew=0
INTERVAL_SECONDS=3600
```

- [ ] **Step 2: Add MONITOR_URL to docker-compose.yml**

In `docker-compose.yml`, add `- MONITOR_URL=${MONITOR_URL}` to the `environment` block:

```yaml
services:
  hardverapro-monitor:
    build: .
    container_name: hardverapro-monitor
    restart: unless-stopped
    environment:
      - RESEND_API_KEY=${RESEND_API_KEY}
      - EMAIL_FROM=${EMAIL_FROM}
      - EMAIL_TO=${EMAIL_TO}
      - MONITOR_URL=${MONITOR_URL}
      - INTERVAL_SECONDS=${INTERVAL_SECONDS}
    volumes:
      - ./data:/app/data
```

- [ ] **Step 3: Add MONITOR_URL to the actual .env file**

Open `.env` and add the line (use the same URL currently hardcoded, or a new search URL):

```
MONITOR_URL=<your desired hardverapro.hu search URL>
```

- [ ] **Step 4: Commit**

```bash
git add env.example docker-compose.yml
git commit -m "feat: add MONITOR_URL to env.example and docker-compose"
```

Note: `.env` is in `.gitignore` and should NOT be staged.
