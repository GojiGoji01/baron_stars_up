# Webhook Mode

## Local polling

```bash
BOT_MODE=polling
python main.py
```

## Production webhook

```bash
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
TELEGRAM_WEBHOOK_PATH=/webhooks/telegram
TELEGRAM_WEBHOOK_SECRET=strong_random_secret
PLATEGA_WEBHOOK_PATH=/webhooks/platega
CRYPTOBOT_WEBHOOK_PATH=/webhooks/cryptobot
CRYPTOBOT_WEBHOOK_SECRET=strong_random_secret
python main.py
```

Telegram webhook URL:

```text
https://your-domain.com/webhooks/telegram
```

Platega callback URL:

```text
https://your-domain.com/webhooks/platega
```

CryptoBot callback URL:

```text
https://your-domain.com/webhooks/cryptobot
```

## Curl examples

Health:

```bash
curl https://your-domain.com/health
```

Platega CONFIRMED:

```bash
curl -X POST https://your-domain.com/webhooks/platega \
  -H "Content-Type: application/json" \
  -H "X-MerchantId: $PLATEGA_MERCHANT_ID" \
  -H "X-Secret: $PLATEGA_SECRET" \
  -d '{"status":"CONFIRMED","transactionId":"TRANSACTION_ID","payload":"ORD00000001"}'
```

Platega CANCELED:

```bash
curl -X POST https://your-domain.com/webhooks/platega \
  -H "Content-Type: application/json" \
  -H "X-MerchantId: $PLATEGA_MERCHANT_ID" \
  -H "X-Secret: $PLATEGA_SECRET" \
  -d '{"status":"CANCELED","transactionId":"TRANSACTION_ID","payload":"ORD00000001"}'
```

CryptoBot paid:

```bash
curl -X POST "https://your-domain.com/webhooks/cryptobot?secret=$CRYPTOBOT_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"update_type":"invoice_paid","payload":{"invoice_id":"INVOICE_ID","status":"paid","payload":"ORD00000001"}}'
```
