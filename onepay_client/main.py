import base64
import hmac
import hashlib
from typing import Any, Dict, List, Literal, Optional
import jwt
import requests
from datetime import datetime


class OnepayResponse:
    def __init__(
        self,
        status: Literal["success", "failed"],
        code: int,
        msg: str,
        data: Any,
    ):
        self.status = status
        self.code = code
        self.msg = msg
        self.data = data


class OnepayException(Exception):
    def __init__(self, message: str, code: int):
        super()
        self.message = message
        self.code = code


class PaymentIntent:
    def __init__(
        self,
        id: str,
        created_at: str,
        updated_at: str,
        deleted_at: Optional[str],
        invoice_number: Optional[str],
        trx_id: Optional[str],
        amount: float,
        currency: str,
        return_url: Optional[str],
        payment_method: Optional[str],
        status: Literal["created", "pending", "received", "success", "failed", "processing", "refunded", "cancelled"],
        renew_id: Optional[str],
        plan_id: Optional[str] = None,
        subscription_status: Optional[Literal["active", "inactive"]] = None,
        next_billing_date: Optional[datetime] = None,
        provider_id: str = "",
        contact_id: str = "",
        merchant_id: str = "",
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        payment_intent: Optional[Dict[str, Any]] = None,
        logs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at
        self.invoice_number = invoice_number
        self.trx_id = trx_id
        self.amount = amount
        self.currency = currency
        self.return_url = return_url
        self.payment_method = payment_method
        self.status = status
        self.renew_id = renew_id
        self.plan_id = plan_id
        self.subscription_status = subscription_status
        self.next_billing_date = next_billing_date
        self.provider_id = provider_id
        self.contact_id = contact_id
        self.merchant_id = merchant_id
        self.ip = ip
        self.user_agent = user_agent
        self.meta_data = meta_data
        self.payment_intent = payment_intent
        self.logs = logs


class PaymentLink:
    def __init__(
        self,
        payment_id: str,
        link: str,
        recurring: bool,
        payment_intent: Optional[PaymentIntent],
    ):
        self.payment_id = payment_id
        self.link = link
        self.recurring = recurring
        self.payment_intent = payment_intent


class PaymentMethodInfo:
    """Represents a payment method nested inside a PaymentProvider."""

    def __init__(self, slug: str, logo: Optional[str] = None, **kwargs):
        self.slug = slug
        self.logo = logo


class PaymentProvider:
    def __init__(
        self,
        id: str,
        name: str,
        slug: Literal["stripe", "razorpay", "billdesk", "xendit"],
        logo: Optional[str],
        description: Optional[str],
        is_recommended: bool,
        payment_methods: Optional[List[dict]] = None,
        **kwargs,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.logo = logo
        self.description = description
        self.is_recommended = is_recommended
        self.payment_methods = [
            PaymentMethodInfo(**pm) for pm in (payment_methods or [])
        ]


class OnepayClient:
    def __init__(self, domain: str, api_key: str, secret_key: str):
        self.domain = domain
        self.api_key = api_key
        self.secret_key = secret_key

    def __request(self, endpoint: str, method: str, data: dict = None):
        time = str(int(datetime.utcnow().timestamp() * 1000))
        token = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                time.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()
        response = requests.request(
            method=method,
            url=self.domain + endpoint,
            headers={
                "Content-Type": "application/json",
                "X-ACCESS-KEY": self.api_key,
                "X-ACCESS-TOKEN": f"{time}:{token}",
            },
            json=data,
            timeout=30,
        )
        try:
            response.raise_for_status()
            return OnepayResponse(**response.json())
        except requests.exceptions.HTTPError as e:
            res = e.response.json()
            raise OnepayException(res["msg"], res["code"]) from e
        except Exception as e:
            raise OnepayException("Unknown error", 500) from e

    # ── Contacts ──────────────────────────────────────────────

    def create_contact(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        country: Optional[str] = None,
    ) -> str:
        data = {
            "name": name,
            "phone": phone,
            "email": email,
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
        }
        res = self.__request(
            method="POST",
            endpoint="/v1/contacts",
            data=data,
        )
        return res.data.get("contact_id")

    def update_contact(
        self,
        contact_id: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        country: Optional[str] = None,
    ):
        data = {
            "name": name,
            "phone": phone,
            "email": email,
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
        }
        self.__request(
            method="PUT",
            endpoint=f"/v1/contacts/{contact_id}",
            data=data,
        )

    # ── Providers & Payment Methods ───────────────────────────

    def get_payment_providers(
        self, ip: Optional[str] = None, country_code: Optional[str] = None
    ):
        endpoint = "/v1/payments/providers?"
        if ip:
            endpoint += f"ip={ip}&"
        if country_code:
            endpoint += f"country_code={country_code}&"
        res = self.__request(
            method="GET",
            endpoint=endpoint,
        )
        return list(map(lambda x: PaymentProvider(**x), res.data))

    def get_payment_methods(
        self, ip: Optional[str] = None, country_code: Optional[str] = None
    ):
        """Retrieve supported payment methods for the merchant based on location."""
        endpoint = "/v1/payments/methods?"
        if ip:
            endpoint += f"ip={ip}&"
        if country_code:
            endpoint += f"country_code={country_code}&"
        res = self.__request(
            method="GET",
            endpoint=endpoint,
        )
        return res.data

    # ── Payments ──────────────────────────────────────────────

    def create_payment(
        self,
        contact_id: str,
        provider: Literal["stripe", "razorpay", "billdesk", "xendit"],
        amount: float,
        currency: str,
        return_url: str,
        ip: str,
        user_agent: str,
        payment_method: Optional[Literal["upi", "card", "netbanking", "wallet"]] = None,
        country_code: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        capture_mode: Optional[Literal["manual", "automatic"]] = None,
        capture_expiry_period: Optional[int] = None,
        refund_speed: Optional[Literal["normal", "optimum"]] = None,
        recurring_conf: Optional[Dict[str, Any]] = None,
    ):
        data = {
            "contact_id": contact_id,
            "provider": provider,
            "amount": amount,
            "currency": currency,
            "return_url": return_url,
            "ip": ip,
            "user_agent": user_agent,
        }
        if payment_method is not None:
            data["payment_method"] = payment_method
        if country_code is not None:
            data["country_code"] = country_code
        if meta_data is not None:
            data["meta_data"] = meta_data
        if capture_mode is not None:
            data["capture_mode"] = capture_mode
        if capture_expiry_period is not None:
            data["capture_expiry_period"] = capture_expiry_period
        if refund_speed is not None:
            data["refund_speed"] = refund_speed
        if recurring_conf is not None:
            data["recurring_conf"] = recurring_conf
        res = self.__request(
            method="POST",
            endpoint="/v1/payments/intent",
            data=data,
        )
        return PaymentLink(
            **res.data,
            payment_intent=PaymentIntent(
                **res.data["payment_intent"]
            ) if res.data.get("payment_intent") else None,
        )

    def get_payment(self, payment_id: str):
        res = self.__request(
            method="GET",
            endpoint=f"/v1/payments/intent/{payment_id}",
        )
        return PaymentIntent(**res.data)

    def capture_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
    ):
        """Capture an authorized payment (manual capture mode)."""
        data: Dict[str, Any] = {"payment_id": payment_id}
        if amount is not None:
            data["amount"] = amount
        res = self.__request(
            method="POST",
            endpoint="/v1/payments/capture",
            data=data,
        )
        return res.data

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        speed: Optional[Literal["normal", "optimum"]] = None,
    ):
        """Initiate a refund for a captured / successful payment."""
        data: Dict[str, Any] = {"payment_id": payment_id}
        if amount is not None:
            data["amount"] = amount
        if speed is not None:
            data["speed"] = speed
        res = self.__request(
            method="POST",
            endpoint="/v1/payments/refund",
            data=data,
        )
        return res.data

    def deactivate_subscription(self, payment_id: str):
        """Deactivate a Xendit recurring subscription plan."""
        res = self.__request(
            method="POST",
            endpoint="/v1/payments/subscription/plan/deactivate",
            data={"payment_id": payment_id},
        )
        return res.data


def decode_webhook_payload(payload: str, signature: str):
    data = jwt.decode(payload, signature, algorithms=["HS256"])
    return PaymentIntent(**data)
