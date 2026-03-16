import json
import math
import requests
import yfinance as yf

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price and basic info for a given ticker symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL, TSLA, TCS.NS",
                    }
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the current exchange rate between two currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code, e.g. USD, EUR, INR",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code, e.g. USD, EUR, INR",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_compound_interest",
            "description": "Calculate compound interest for an investment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "number",
                        "description": "Initial investment amount in dollars",
                    },
                    "annual_rate": {
                        "type": "number",
                        "description": "Annual interest rate as a percentage, e.g. 8 for 8%",
                    },
                    "years": {
                        "type": "number",
                        "description": "Number of years to invest",
                    },
                    "compounds_per_year": {
                        "type": "integer",
                        "description": "Number of times interest compounds per year (default 12 for monthly)",
                        "default": 12,
                    },
                },
                "required": ["principal", "annual_rate", "years"],
            },
        },
    },
]


def get_stock_price(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d")

        if hist.empty:
            return {"error": f"No data found for ticker '{ticker}'"}

        current_price = hist["Close"].iloc[-1]
        result = {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2),
            "currency": info.get("currency", "USD"),
            "company_name": info.get("longName", ticker),
            "market_cap": info.get("marketCap"),
            "previous_close": info.get("previousClose"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
        }
        if result["previous_close"]:
            change = current_price - result["previous_close"]
            change_pct = (change / result["previous_close"]) * 100
            result["change"] = round(change, 2)
            result["change_percent"] = round(change_pct, 2)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    try:
        url = f"https://open.er-api.com/v6/latest/{from_currency.upper()}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("result") != "success":
            return {"error": f"Failed to fetch rates for {from_currency}"}

        to_upper = to_currency.upper()
        if to_upper not in data["rates"]:
            return {"error": f"Currency '{to_currency}' not found"}

        rate = data["rates"][to_upper]
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_upper,
            "rate": round(rate, 6),
            "last_updated": data.get("time_last_update_utc", "unknown"),
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    years: float,
    compounds_per_year: int = 12,
) -> dict:
    r = annual_rate / 100
    n = compounds_per_year
    t = years

    final_amount = principal * (1 + r / n) ** (n * t)
    total_interest = final_amount - principal

    return {
        "principal": round(principal, 2),
        "annual_rate_percent": annual_rate,
        "years": years,
        "compounds_per_year": compounds_per_year,
        "final_amount": round(final_amount, 2),
        "total_interest_earned": round(total_interest, 2),
        "total_return_percent": round((total_interest / principal) * 100, 2),
    }


def run_tool(name: str, args: dict) -> str:
    if name == "get_stock_price":
        result = get_stock_price(**args)
    elif name == "get_exchange_rate":
        result = get_exchange_rate(**args)
    elif name == "calculate_compound_interest":
        result = calculate_compound_interest(**args)
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)
