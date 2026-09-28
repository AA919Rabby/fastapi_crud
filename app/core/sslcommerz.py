import httpx
from app.core.config import settings

class SSLCommerzService:
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASS
        # Correct sandbox URL endpoint
        if settings.SSLCOMMERZ_IS_SANDBOX:
            self.session_api = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_api = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
        else:
            self.session_api = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_api = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"

    async def init_payment(
        self,
        tran_id: str,
        total_amount: float,
        cus_name: str,
        cus_email: str,
        cus_phone: str,
        cus_address: str,
        service_title: str
    ) -> dict:
        base_url = settings.BACKEND_BASE_URL.rstrip('/')

        payload = {
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "total_amount": str(round(float(total_amount), 2)),
            "currency": "BDT",
            "tran_id": tran_id,
            "success_url": f"{base_url}/api/v1/services/payment/success",
            "fail_url": f"{base_url}/api/v1/services/payment/fail",
            "cancel_url": f"{base_url}/api/v1/services/payment/cancel",
            "ipn_url": f"{base_url}/api/v1/payment/ipn",
            "cus_name": cus_name if cus_name else "Valued Customer",
            "cus_email": cus_email if cus_email else "customer@example.com",
            "cus_add1": cus_address if cus_address else "Dhaka, Bangladesh",
            "cus_city": "Dhaka",
            "cus_country": "Bangladesh",
            "cus_phone": cus_phone if cus_phone else "01700000000",
            "shipping_method": "NO",
            "product_name": service_title if service_title else "Service Booking",
            "product_category": "HomeService",
            "product_profile": "general"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.post(self.session_api, data=payload)

                # Check if response returned valid text
                if not resp.text or resp.status_code != 200:
                    return {"status": "FAILED", "failedreason": f"HTTP {resp.status_code}: {resp.text}"}

                data = resp.json()
                return data
        except Exception as e:
            print(f">>> [SSLCOMMERZ ERROR]: {e}")
            return {"status": "FAILED", "failedreason": str(e)}

    async def validate_transaction(self, val_id: str) -> dict:
        params = {
            "val_id": val_id,
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(self.validation_api, params=params)
                return resp.json()
        except Exception as e:
            return {"status": "FAILED", "failedreason": str(e)}

ssl_client = SSLCommerzService()