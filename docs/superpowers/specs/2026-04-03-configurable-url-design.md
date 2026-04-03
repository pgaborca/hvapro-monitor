# Configurable Search URL — Design Spec

**Date:** 2026-04-03
**Status:** Approved

## Summary

Replace the hardcoded Hardverapro search URL with a required `MONITOR_URL` environment variable. Generalize hardcoded email copy so the monitor works for any search, not just iPhone 16 Pro.

## Changes

### `hardverapro_monitor.py`

- Replace the hardcoded `"url"` value in `CONFIG` with `os.environ.get("MONITOR_URL", "")`.
- Add `"monitor_url"` (mapped from `MONITOR_URL`) to the required-vars check in `main()` so the app exits with a clear error if unset.
- Email subject: replace `"[Hardverapro] {count} új hirdetés – iPhone 16 Pro keresett"` with `"[Hardverapro] {count} új hirdetés"`.
- Email HTML subtitle: replace `"iPhone 16 Pro • keresett • 210 000 – 250 000 Ft"` with the value of `MONITOR_URL`.
- Email plain-text preamble: replace `"Új Hardverapro hirdetések – iPhone 16 Pro keresett (210k–250k Ft)"` with `"Új Hardverapro hirdetések"`.

### `env.example`

Add:
```
MONITOR_URL=https://hardverapro.hu/aprok/mobil/mobil/iphone/iphone_16/iphone_16_pro/keres.php?stext=&minprice=210000&maxprice=250000&__buying=1&__buying=0&__brandnew=1&__brandnew=0
```

### `docker-compose.yml`

Add to the `environment` block:
```yaml
- MONITOR_URL=${MONITOR_URL}
```

## Out of Scope

- Multiple URLs / multiple searches in parallel
- A `MONITOR_LABEL` variable for custom email subjects
- CLI argument support
