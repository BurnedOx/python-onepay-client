import base64
import hmac
import hashlib
from typing import Any, Dict, Literal, Optional
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
        status: Literal["pending", "success", "failed", "processing", "refunded", "cancelled"],
        renew_id: Optional[str],
        provider_id: str,
        contact_id: str,
        merchant_id: str,
        ip: Optional[str],
        user_agent: Optional[str],
        meta_data: Optional[Dict[str, Any]],
        payment_intent: Optional[Dict[str, Any]],
        logs: Optional[Dict[str, Any]],
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
    ):
        self.payment_id = payment_id
        self.link = link


class PaymentProvider:
    def __init__(
        self,
        id: str,
        name: str,
        slug: Literal["stripe", "razorpay", "billdesk"],
        logo: Optional[str],
        description: Optional[str],
        is_recommended: bool,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.logo = logo
        self.description = description
        self.is_recommended = is_recommended


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

    def get_payment_providers(self, ip: str):
        res = self.__request(
            method="GET",
            endpoint=f"/v1/payments/providers?ip={ip}",
        )
        return list(map(lambda x: PaymentProvider(**x), res.data))

    def create_payment(
        self,
        contact_id: str,
        provider: Literal["stripe", "razorpay", "billdesk"],
        amount: float,
        currency: str,
        return_url: str,
        ip: str,
        user_agent: str,
        meta_data: Optional[Dict[str, Any]] = None,
    ):
        data = {
            "contact_id": contact_id,
            "provider": provider,
            "amount": amount,
            "currency": currency,
            "return_url": return_url,
            "ip": ip,
            "user_agent": user_agent,
            "meta_data": meta_data,
        }
        res = self.__request(
            method="POST",
            endpoint="/v1/payments/intent",
            data=data,
        )
        return PaymentLink(**res.data)

    def get_payment(self, payment_id: str):
        res = self.__request(
            method="GET",
            endpoint=f"/v1/payments/intent/{payment_id}",
        )
        return PaymentIntent(**res.data)


def decode_webhook_payload(payload: str, signature: str):
    data = jwt.decode(payload, signature, algorithms=["HS256"])
    return PaymentIntent(**data)
