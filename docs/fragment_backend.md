# Fragment Backend Notes

This Telegram bot repository does not contain browser automation for Fragment.
It does not open Fragment pages, click buttons, or perform additional UI steps
before `Buy`.

Fragment delivery in this repo is limited to passing the following data to the
external Fragment API backend:

- `seed`
- `cookies`
- `local_storage`
- `wait=True`

If the external backend returns `Buy button is disabled`, the issue must be
debugged in the external Fragment API backend / Playwright automation layer or
by refreshing Fragment wallet session state (`cookies` / `localStorage`).

## Fragment config check

Run this on the server:

```bash
cd /opt/tg_star
/opt/tg_star/.venv/bin/python - <<'PY'
from app.services.fragment.client import FragmentAPIService
from config import settings

service = FragmentAPIService(
    wallet_mnemonic=settings.fragment_wallet_mnemonic,
    api_url=settings.fragment_effective_api_url,
    api_mode=settings.fragment_api_mode,
    cookies_base64=settings.fragment_cookies_base64,
    local_storage_base64=settings.fragment_local_storage_base64,
)
print(service.get_debug_info())
PY
```

Expected keys:

- `fragment_api_url_present`
- `fragment_wallet_mnemonic_present`
- `fragment_cookies_present`
- `fragment_local_storage_present`
- `fragment_api_mode`
- `fragment_sdk_available`

## localStorage check

Open `fragment.com` in a normal browser and run this in DevTools Console:

```js
Object.fromEntries(
  Array.from({ length: localStorage.length }, (_, i) => {
    const key = localStorage.key(i);
    return [key, localStorage.getItem(key)];
  })
)
```

To export only TonConnect keys:

```js
Object.fromEntries(
  Array.from({ length: localStorage.length }, (_, i) => {
    const key = localStorage.key(i);
    return [key, localStorage.getItem(key)];
  }).filter(([key]) => key.startsWith("ton-connect"))
)
```

## Retry delivery

This repo supports retrying delivery for already-paid orders without creating a
new invoice or changing Platega payment status.

Admin callback:

- `admin:retry:<order_id>`

Programmatic retry:

```bash
cd /opt/tg_star
/opt/tg_star/.venv/bin/python - <<'PY'
import asyncio
from app.db.session import session_scope
from app.services.checkout import retry_delivery

ORDER_ID = 1

async def main():
    async with session_scope() as session:
        result = await retry_delivery(session, order_id=ORDER_ID)
        print({
            "order_id": result.order.order_id,
            "status": result.order.status,
            "delivery_status": result.order.delivery_status,
            "payment_status": result.payment_status,
            "user_message": result.user_message,
        })

asyncio.run(main())
PY
```

Behavior:

- does not create a new invoice
- does not modify Platega payment status
- uses the current order
- respects idempotency for completed orders
- respects current delivery-attempt limits

## Example success log

```text
fragment_buy_stars_started username=@user amount=50 mode=kyc has_cookies=True has_local_storage=True
fragment_purchase_completed transaction_id=abc123
```

## Example disabled buy error

```text
fragment_buy_stars_started username=@user amount=50 mode=kyc has_cookies=True has_local_storage=True
fragment_delivery_failed order_id=7 error_type=FragmentAPIError retryable=False
```

User/admin-facing message:

```text
Оплата получена, но Fragment backend не смог выполнить покупку Stars: Buy button is disabled. Проверьте аккаунт Fragment, TON balance, wallet session, cookies/localStorage или внешний automation backend.
```

## What to send to the external backend owner

- exact `buy_stars()` error text
- whether manual purchase works from the same wallet
- `service.get_debug_info()` output
- whether `sessionStorage` is empty
- list of TonConnect keys in `localStorage`
- request to inspect the automation state before clicking `Buy`:
  - screenshot
  - current page URL
  - Buy button text
  - `disabled` / `aria-disabled`
  - visibility of `Connect wallet`
