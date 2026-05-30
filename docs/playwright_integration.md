# Playwright Integration

This repository uses Playwright as an isolated browser/session layer. It does
not replace the existing bot architecture, routers, payment flow, or database
logic.

## What is added

- `app/services/browser.py`
- persistent Chromium context via `launch_persistent_context()`
- session reuse across restarts through `./userdata`
- startup/shutdown integration in `main.py`

## Environment variables

```env
PLAYWRIGHT_ENABLED=true
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_NO_SANDBOX=true
PLAYWRIGHT_USERDATA_DIR=./userdata
PLAYWRIGHT_LAUNCH_TIMEOUT_MS=30000
```

For Linux VPS, `PLAYWRIGHT_NO_SANDBOX=true` keeps the required launch arg:

```python
args=["--no-sandbox"]
```

## Install

Python dependency:

```bash
pip install -r requirements.txt
```

Browser binary:

```bash
playwright install chromium
```

## Startup flow

`main.py` starts Playwright before polling/webhook mode and closes it on
shutdown. The browser layer is isolated and can be reused by existing services.

## Example usage

Inside existing bot logic:

```python
from app.services.browser import get_browser_manager

browser = get_browser_manager()
page = await browser.new_page()
await page.goto("https://fragment.com", wait_until="domcontentloaded")
```

Fragment browser session debug:

```python
from app.services.fragment.client import FragmentAPIService
from config import settings

service = FragmentAPIService(
    wallet_mnemonic=settings.fragment_wallet_mnemonic,
    api_url=settings.fragment_effective_api_url,
    api_mode=settings.fragment_api_mode,
    cookies_base64=settings.fragment_cookies_base64,
    local_storage_base64=settings.fragment_local_storage_base64,
)
debug = await service.collect_browser_debug_info()
print(debug)
```

Fragment browser preflight before external SDK call:

```python
from app.services.fragment.client import FragmentAPIService
from config import settings

service = FragmentAPIService(
    wallet_mnemonic=settings.fragment_wallet_mnemonic,
    api_url=settings.fragment_effective_api_url,
    api_mode=settings.fragment_api_mode,
    cookies_base64=settings.fragment_cookies_base64,
    local_storage_base64=settings.fragment_local_storage_base64,
)
preflight = await service.collect_browser_preflight_info()
print(preflight)
```

Fragment buy page probe for a specific recipient:

```python
from app.services.fragment.client import FragmentAPIService
from config import settings

service = FragmentAPIService(
    wallet_mnemonic=settings.fragment_wallet_mnemonic,
    api_url=settings.fragment_effective_api_url,
    api_mode=settings.fragment_api_mode,
    cookies_base64=settings.fragment_cookies_base64,
    local_storage_base64=settings.fragment_local_storage_base64,
)
probe = await service.probe_buy_page(username="@durov", amount=50)
print(probe)
```

The preflight now first syncs `FRAGMENT_COOKIES_BASE64` and
`FRAGMENT_LOCAL_STORAGE_BASE64` into the persistent Playwright session and only
then checks Fragment page state.

Before the final preflight snapshot, the bot also performs a lightweight
session warmup: it reloads Fragment up to three times and checks whether the
wallet-connected state becomes visible to the page runtime.

This collects:

- current Fragment URL
- page title
- `Connect TON` / `Connect wallet` visibility
- localStorage keys
- sessionStorage keys
- body text excerpt
- screenshot path

The preflight additionally reports:

- `fragment_wallet_session_ready`
- `fragment_ton_connect_key_count`
- `fragment_session_sync`
- `fragment_warmup`
- screenshot path before the external SDK buy call

The buy page probe additionally reports:

- candidate URLs that were tried
- whether a `Buy` button was found
- `Buy` button text
- `disabled`
- `aria-disabled`
- `next_step_probe` after clicking `Buy Stars Package`, when that CTA is present

Inside Fragment debug/config flow:

```python
service.get_debug_info()
```

It includes:

- `playwright_enabled`
- `playwright_context_started`

## Notes

- Session data is stored in `./userdata`
- `FRAGMENT_COOKIES_BASE64` and `FRAGMENT_LOCAL_STORAGE_BASE64` are synced into
  the persistent browser context before preflight checks
- Existing handlers, routers, DB logic, and configs remain untouched
- This repo still does not implement Fragment UI automation by itself unless
  you explicitly build it on top of `BrowserManager`
- `buy_stars()` now performs a safe preflight check and logs browser session
  state before calling the external Fragment SDK
