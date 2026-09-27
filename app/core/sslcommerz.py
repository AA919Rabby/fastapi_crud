import httpx
from app.core.config import settings

class SSLCommerzService:
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASS
        if settings.SSLCOMMERZ_IS_SANDBOX:
            self.session_api = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
        else:
            self.session_api = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"

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
        payload = {
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "total_amount": str(total_amount),
            "currency": "BDT",
            "tran_id": tran_id,
            "success_url": f"{settings.BACKEND_BASE_URL}/api/v1/services/payment/success",
            "fail_url": f"{settings.BACKEND_BASE_URL}/api/v1/services/payment/fail",
            "cancel_url": f"{settings.BACKEND_BASE_URL}/api/v1/services/payment/cancel",
            "ipn_url": f"{settings.BACKEND_BASE_URL}/api/v1/services/payment/ipn",
            "cus_name": cus_name or "Customer",
            "cus_email": cus_email or "customer@example.com",
            "cus_add1": cus_address or "Dhaka, Bangladesh",
            "cus_city": "Dhaka",
            "cus_country": "Bangladesh",
            "cus_phone": cus_phone or "01700000000",
            "shipping_method": "NO",
            "product_name": service_title,
            "product_category": "Service",
            "product_profile": "general"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.session_api, data=payload)
                data = resp.json()
                print(f"\n>>> [SSLCOMMERZ RESPONSE]: {data}\n")
                return data
        except Exception as e:
            print(f">>> [SSLCOMMERZ ERROR]: {e}")
            return {"status": "FAILED", "failedreason": str(e)}

ssl_client = SSLCommerzService()