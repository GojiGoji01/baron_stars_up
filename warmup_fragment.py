import asyncio
import logging
import os
from pathlib import Path

from playwright.async_api import async_playwright

from app.logging import setup_logging
from config import settings


setup_logging()
logger = logging.getLogger(__name__)

LOGIN_URL = f"{settings.fragment_web_base_url.rstrip('/')}/"
CHECK_URL = f"{settings.fragment_web_base_url.rstrip('/')}/stars/buy?amount=50"


async def main() -> None:
    userdata_dir = Path(settings.playwright_userdata_dir).resolve()
    userdata_dir.mkdir(parents=True, exist_ok=True)

    launch_args = ["--start-maximized"]
    if settings.playwright_no_sandbox:
        launch_args.append("--no-sandbox")

    logger.info(
        "fragment_warmup_started browser_mode=warmup profile=%s headless=%s",
        userdata_dir,
        False,
    )
    if not os.environ.get("DISPLAY"):
        logger.warning("fragment_warmup_display_missing DISPLAY is not set; use xvfb-run or VNC")

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(userdata_dir),
            headless=False,
            args=launch_args,
            viewport={"width": 1440, "height": 900},
            timeout=settings.playwright_launch_timeout_ms,
        )

        page = await context.new_page()

        try:
            print(f"Opening Fragment warmup with profile: {userdata_dir}")
            print("browser_mode=warmup")

            await page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )
            await page.wait_for_timeout(1000)
            await page.goto(
                CHECK_URL,
                wait_until="domcontentloaded",
                timeout=settings.fragment_browser_timeout_ms,
            )

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
            logger.info("fragment_warmup_saved profile=%s", userdata_dir)

            print("Done.")
            print(f"Session saved into {userdata_dir}")
        finally:
            await context.close()
            logger.info("fragment_warmup_finished profile=%s", userdata_dir)


if __name__ == "__main__":
    asyncio.run(main())
