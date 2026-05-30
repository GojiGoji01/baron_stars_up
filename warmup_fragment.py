import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

from config import settings


LOGIN_URL = "https://fragment.com/"
CHECK_URL = "https://fragment.com/stars/buy?amount=50"


async def main():
    userdata_dir = Path(settings.playwright_userdata_dir).resolve()
    userdata_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(userdata_dir),
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1440, "height": 900},
        )

        page = await context.new_page()

        print(f"Opening Fragment warmup with profile: {userdata_dir}")
        print("browser_mode=warmup")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        await page.goto(CHECK_URL, wait_until="domcontentloaded")

        print()
        print("===================================================")
        print("1. Log in to Telegram/Fragment if requested")
        print("2. Click Connect TON")
        print("3. Connect Tonkeeper")
        print("4. Wait until the BUY button becomes active")
        print("5. Do not close the browser window manually")
        print("===================================================")
        print()
        print("When the session is ready, press ENTER here to save it.")

        input()

        print("Saving session state...")
        await context.storage_state(path="fragment_state.json")
        await context.close()

        print("Done.")
        print(f"Session saved into {userdata_dir}")


asyncio.run(main())
