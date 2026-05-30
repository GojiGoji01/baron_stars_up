import asyncio
import os

from playwright.async_api import async_playwright


USERDATA = "/opt/tg_star/userdata"
LOGIN_URL = "https://fragment.com/"
CHECK_URL = "https://fragment.com/stars/buy?amount=50"


async def main() -> None:
    if not os.environ.get("DISPLAY"):
        print("DISPLAY is not set. Run with DISPLAY=:99 (Xvfb/VNC).")
        return

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=USERDATA,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        page = await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        await page.goto(CHECK_URL, wait_until="domcontentloaded")

        print("\nDo login manually:")
        print("1. Telegram login")
        print("2. Connect TON / Tonkeeper")
        print("3. Reach state where BUY is active")

        input("\nPress ENTER when done...")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
