import asyncio
from playwright.async_api import async_playwright

USERDATA = "/opt/tg_star/userdata"  # или userdata_fragment — ВЫБЕРИ ОДИН

async def main():
    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=USERDATA,
            headless=True,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        page = await context.new_page()

        await page.goto("https://fragment.com")

        print("\n👉 Сделай login вручную:")
        print("1. Telegram login")
        print("2. Connect TON / Tonkeeper")
        print("3. Дойди до состояния где BUY активен")

        input("\n⛔ Нажми ENTER когда всё готово...")

        await context.close()

asyncio.run(main())