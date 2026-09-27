import json
from google import genai
from google.genai import types
from app.core.config import settings

def run_gemini_service_assistant(user_prompt: str, available_services: list) -> dict:
    if not settings.GEMINI_API_KEY:
        return {
            "reply": "Something went wrong.",
            "suggested_action": None,
            "order_details": None
        }

    catalog_context = "\n".join([
        f"- ID: {s['id']}, Title: '{s['title']}', Category: '{s['category']}', Price: {s['price_bdt']} BDT, Stock Available: {s['stock']}, Team: {s['service_persons']} person(s), Location: {s['location_area']}"
        for s in available_services
    ])

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    system_instruction = f"""
    You are an intelligent Bangladeshi home service assistant.
    Available Services Catalog:
    {catalog_context}

    CRITICAL RULES:
    1. You CAN assist the user with service details and draft an order if they provide: Service ID/Title, Delivery Address in Bangladesh, and Phone Number.
    2. You CANNOT execute or click payment. You must tell the user: 'I have drafted your order, please complete your payment via SSLCommerz.'
    3. Return your response ONLY as a JSON object:
       {{
         "reply": "<your friendly natural response>",
         "can_order": <true if service_id, address, and phone number are all present, else false>,
         "service_id": <service id or null>,
         "service_address": <detected address or null>,
         "customer_phone": <detected phone or null>
       }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return {
            "reply": data.get("reply", "How may I help you?"),
            "suggested_action": "CONFIRM_ORDER" if data.get("can_order") else None,
            "order_details": {
                "service_id": data.get("service_id"),
                "service_address": data.get("service_address"),
                "customer_phone": data.get("customer_phone")
            } if data.get("can_order") else None
        }
    except Exception as e:
        return {
            "reply": f"AI Assistant unavailable: {str(e)}",
            "suggested_action": None,
            "order_details": None
        }