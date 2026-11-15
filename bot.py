
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

NSE_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_PAGE = "https://www.nseindia.com/reports/fii-dii"

def get_fii_dii():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": NSE_PAGE,
    })

    # Establish NSE session before requesting its data
    session.get(NSE_PAGE, timeout=20)
    response = session.get(NSE_URL, timeout=20)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list) or not data:
        raise ValueError("NSE returned no FII/DII records")

    result = {}
    for item in data:
        category = str(item.get("category", "")).upper()
        if "FII" in category or "FPI" in category:
            key = "FII"
        elif "DII" in category:
            key = "DII"
        else:
            continue

        result[key] = {
            "date": item.get("date", ""),
            "buy": float(str(item.get("buyValue", "0")).replace(",", "")),
            "sell": float(str(item.get("sellValue", "0")).replace(",", "")),
            "net": float(str(item.get("netValue", "0")).replace(",", "")),
        }

    if "FII" not in result or "DII" not in result:
        raise ValueError("FII or DII data missing; report not sent")

    return result


def format_report(data):
    fii = data["FII"]
    dii = data["DII"]

    report_date = fii["date"] or dii["date"] or "Date unavailable"

    def line(name, values):
        return (
            f"{name}\n"
            f"Buy: ₹{values['buy']:,.2f} Cr\n"
            f"Sell: ₹{values['sell']:,.2f} Cr\n"
            f"Net: ₹{values['net']:,.2f} Cr"
        )

    combined = fii["net"] + dii["net"]

    sentiment = (
        "Institutional net buying"
        if combined > 0 else
        "Institutional net selling"
        if combined < 0 else
        "Institutional flows balanced"
    )

    return (
        "📊 FII / DII DAILY REPORT\n"
        f"📅 Date: {report_date}\n\n"
        f"{line('🔴 FII / FPI', fii)}\n\n"
        f"{line('🟢 DII', dii)}\n\n"
        f"Combined Net: ₹{combined:,.2f} Cr\n"
        f"Market Flow: {sentiment}\n\n"
        "Source: NSE India\n"
        "https://www.nseindia.com/reports/fii-dii\n\n"
        "Note: Provisional cash-market data."
    )


def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=20
    )
    response.raise_for_status()

    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected the message")


if __name__ == "__main__":
    report = get_fii_dii()
    send_telegram(format_report(report))
    print("FII/DII report sent successfully.")
