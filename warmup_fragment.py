import asyncio
from playwright.async_api import async_playwright

URL = "https://fragment.com/stars/buy?amount=50"

async def main():
    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir="./userdata_fragment",
            headless=False,
            args=[
                "--start-maximized"
            ],
            viewport={"width": 1440, "height": 900}
        )

        page = await context.new_page()

        print("Открываю Fragment...")

        await page.goto(URL)

        print()
        print("===================================================")
        print("1. Войди в Telegram/Fragment")
        print("2. Нажми Connect TON")
        print("3. Подключи Tonkeeper")
        print("4. Дойди до состояния, где кнопка BUY активна")
        print("5. НЕ закрывай браузер крестиком")
        print("===================================================")
        print()
        print("Когда всё готово -> нажми ENTER в терминале")

        input()

        print("Сохраняю профиль...")

        await context.storage_state(path="fragment_state.json")

        await context.close()

        print("Готово.")
        print("Профиль сохранён в ./userdata_fragment")

asyncio.run(main())

