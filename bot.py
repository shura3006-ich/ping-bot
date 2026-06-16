import asyncio
import aiohttp
import os
import time
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # секунд

SERVERS = [
    # fitexpress
    {"name": "FitExpress Main",   "url": "https://fitexpress.space",           "group": "fitexpress"},
    {"name": "FitExpress ATS",    "url": "https://ats.fitexpress.space",        "group": "fitexpress"},
    {"name": "Analyzavr",         "url": "https://analyzer.analyzavr.space",    "group": "fitexpress"},
    # teravita
    {"name": "Terravita Store",   "url": "https://terravita.store",             "group": "teravita"},
    {"name": "Terravita Droid",   "url": "https://droid.terravita.store",       "group": "teravita"},
    {"name": "Terravita ATS",     "url": "https://ats.terravita.store",         "group": "teravita"},
    {"name": "Terravita PP",      "url": "https://pp.terravita.store",          "group": "teravita"},
    # sell1.best
    {"name": "Sell1 Main",        "url": "https://sell1.best",                  "group": "sell1.best"},
    {"name": "Sell1 Agregator",   "url": "https://agregator.sell1.best",        "group": "sell1.best"},
    {"name": "Sell1 ATS",         "url": "https://ats.sell1.best",              "group": "sell1.best"},
    {"name": "Nutra1",            "url": "https://nutra1.top",                  "group": "sell1.best"},
    # densys
    {"name": "Densys Server",     "url": "http://173.242.49.191",               "group": "densys"},
]

# Хранит предыдущий статус каждого сервера
prev_status = {}  # url -> True/False


async def send_telegram(session, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"Telegram error: {await resp.text()}")
    except Exception as e:
        print(f"Telegram send failed: {e}")


async def check_server(session, srv):
    start = time.monotonic()
    try:
        async with session.get(
            srv["url"],
            timeout=aiohttp.ClientTimeout(total=8),
            allow_redirects=True,
            ssl=False  # не падать на самоподписанных сертификатах
        ) as resp:
            ms = int((time.monotonic() - start) * 1000)
            return True, ms
    except Exception:
        ms = int((time.monotonic() - start) * 1000)
        return False, ms


async def check_all(session):
    now = datetime.now().strftime("%H:%M:%S")
    tasks = [check_server(session, srv) for srv in SERVERS]
    results = await asyncio.gather(*tasks)

    for srv, (is_up, ms) in zip(SERVERS, results):
        url = srv["url"]
        was_up = prev_status.get(url, None)

        if was_up is None:
            # первый запуск — просто запоминаем, не шумим
            prev_status[url] = is_up
            status = "✅" if is_up else "❌"
            print(f"[{now}] {status} {srv['name']} — {ms}ms")
            continue

        if is_up and not was_up:
            # поднялся!
            msg = (
                f"✅ <b>{srv['name']}</b> снова онлайн\n"
                f"🕐 {now}\n"
                f"⚡ {ms} ms\n"
                f"🔗 {url}"
            )
            await send_telegram(session, msg)
            print(f"[{now}] ✅ RECOVERED: {srv['name']}")

        elif not is_up and was_up:
            # упал!
            msg = (
                f"🔴 <b>{srv['name']}</b> недоступен!\n"
                f"🕐 {now}\n"
                f"📁 Группа: {srv['group']}\n"
                f"🔗 {url}"
            )
            await send_telegram(session, msg)
            print(f"[{now}] ❌ DOWN: {srv['name']}")

        else:
            status = "✅" if is_up else "❌"
            print(f"[{now}] {status} {srv['name']} — {ms}ms")

        prev_status[url] = is_up


async def main():
    print(f"🚀 Ping Monitor Bot запущен. Интервал: {CHECK_INTERVAL}с")
    print(f"📡 Мониторим {len(SERVERS)} серверов\n")

    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Стартовое сообщение
        await send_telegram(session, f"🚀 <b>Ping Monitor запущен</b>\n📡 Мониторю {len(SERVERS)} серверов\n⏱ Интервал проверки: {CHECK_INTERVAL}с")

        while True:
            await check_all(session)
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
