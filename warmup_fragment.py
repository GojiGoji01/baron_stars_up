import asyncio

from playwright.async_api import async_playwright


USERDATA = "/opt/tg_star/userdata"


async def main() -> None:
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

        await page.goto("https://fragment.com")

        print("\nDo manual login:")
        print("1. Telegram login")
        print("2. Connect TON / Tonkeeper")
        print("3. Reach state where BUY is active")

        input("\nPress ENTER when done...")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
