# services/gold_price.py

import os
import httpx

# Ideally load from ENV, not hardcode
GOLD_API_KEY = os.getenv("GOLD_API_KEY")
GOLD_API_URL = "https://www.goldapi.io/api/XAU/INR"  # Gold price in INR

async def get_live_gold_price() -> float:
    """
    Fetch live gold price in USD per ounce from GoldAPI.io

    Returns:
        float: Current gold price in USD, or -1.0 on failure.
    """
    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(GOLD_API_URL, headers=headers)
            response.raise_for_status()

            # ✅ Must await JSON
            data = response.json()
            if callable(data):  # sanity check
                data = await response.json()

            price = data.get("price_gram_24k")  # Price per gram in INR

            if price:
                return float(round(price, 2))  # Round to 2 decimal places
            else:
                return -1.0
        except Exception as e:
            print(f"[Gold Price API Error]: {e}")
            return -1.0
