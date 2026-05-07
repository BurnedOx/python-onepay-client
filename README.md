# onepay_client

Python SDK for the OnePay Payments API. Provides a simple, typed interface for managing contacts, creating payments, handling captures/refunds, managing subscriptions, and verifying webhooks.

## Installation

```bash
pip install git+https://github.com/BurnedOx/python-onepay-client.git
```

## Requirements

- Python >= 3.7
- `requests`
- `PyJWT`

## Quick Start

```python
from onepay_client import OnepayClient

client = OnepayClient(
    domain="https://api.yourdomain.com",
    api_key="YOUR_PUBLIC_KEY",
    secret_key="YOUR_PRIVATE_KEY",
)
```

## Usage

### Contacts

```python
# Create a contact
contact_id = client.create_contact(
    name="John Doe",
    email="john@example.com",
    phone="+919876543210",
    country="IN",
)

# Update a contact
client.update_contact(
    contact_id=contact_id,
    name="John D.",
    city="Mumbai",
)
```

### Providers & Payment Methods

```python
# Get available payment providers for a region
providers = client.get_payment_providers(country_code="IN")

for provider in providers:
    print(f"{provider.name} ({provider.slug})")
    for pm in provider.payment_methods:
        print(f"  - {pm.slug}")

# Get available payment methods
methods = client.get_payment_methods(country_code="IN")
```

### Create a Payment

```python
result = client.create_payment(
    contact_id=contact_id,
    provider="razorpay",
    amount=499.00,
    currency="INR",
    return_url="https://yourdomain.com/payment/callback",
    ip="103.21.58.1",
    user_agent="Mozilla/5.0...",
    payment_method="upi",            # optional: "upi" | "card" | "netbanking" | "wallet"
    capture_mode="automatic",         # optional: "manual" | "automatic" (default)
    meta_data={"order_id": "ORD123"}, # optional: custom metadata
)

print(result.payment_id)  # Internal payment ID
print(result.link)         # Redirect the user to this URL to complete payment
```

### Create a Recurring / Subscription Payment

```python
result = client.create_payment(
    contact_id=contact_id,
    provider="xendit",
    amount=99.00,
    currency="USD",
    return_url="https://yourdomain.com/subscription/callback",
    ip="103.21.58.1",
    user_agent="Mozilla/5.0...",
    recurring_conf={
        "interval": "MONTH",
        "interval_count": 1,
        "total_recurrence": 12,
    },
)

print(result.recurring)  # True
```

### Get Payment Status

```python
payment = client.get_payment(payment_id="...")

print(payment.status)  # "created" | "pending" | "received" | "success" | "failed" | ...
```

### Capture a Payment (Manual Mode)

```python
# Full capture
result = client.capture_payment(payment_id="...")

# Partial capture
result = client.capture_payment(payment_id="...", amount=200.00)
```

### Refund a Payment

```python
# Full refund
result = client.refund_payment(payment_id="...")

# Partial refund with optimum speed
result = client.refund_payment(
    payment_id="...",
    amount=100.00,
    speed="optimum",
)
```

### Deactivate a Subscription

```python
result = client.deactivate_subscription(payment_id="...")
```

## Webhook Verification

When OnePay sends a webhook to your server, the payload is a JWT signed with your webhook secret. Use `decode_webhook_payload` to verify and decode it.

```python
from onepay_client import decode_webhook_payload

# In your webhook handler (e.g. Flask / FastAPI)
def handle_webhook(request_body: dict):
    token = request_body["payload"]
    webhook_secret = "YOUR_WEBHOOK_SECRET"

    payment = decode_webhook_payload(token, webhook_secret)

    print(payment.id)      # Internal payment ID
    print(payment.status)  # e.g. "success", "failed", "refunded"
    print(payment.amount)
```

## Error Handling

All API errors raise `OnepayException` with `code` and `message` attributes.

```python
from onepay_client import OnepayException

try:
    client.get_payment("invalid-id")
except OnepayException as e:
    print(f"Error {e.code}: {e.message}")
```

## Available Types

| Class | Description |
|---|---|
| `OnepayClient` | Main SDK client |
| `PaymentIntent` | Full payment record returned by `get_payment()` and webhook decode |
| `PaymentLink` | Result of `create_payment()` — contains `payment_id`, `link`, and the intent |
| `PaymentProvider` | Provider object from `get_payment_providers()` |
| `PaymentMethodInfo` | Payment method nested inside a provider (slug + logo) |
| `OnepayResponse` | Raw API response wrapper |
| `OnepayException` | Error raised on API failures |
| `decode_webhook_payload` | Standalone function to verify & decode webhook JWTs |

## License

MIT
