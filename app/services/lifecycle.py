from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable

from app.services.browser import get_browser_manager


logger = logging.getLogger(__name__)


class ShutdownManager:
    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._signal_name: str | None = None
        self._triggered = False

    def install(self) -> None:
        loop = asyncio.get_running_loop()
        for signum in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(signum, self._request_shutdown, signum)
            except NotImplementedError:
                logger.warning("signal_handler_not_supported signal=%s", signum)

    async def wait(self) -> None:
        await self._shutdown_event.wait()

    @property
    def triggered(self) -> bool:
        return self._triggered

    @property
    def signal_name(self) -> str | None:
        return self._signal_name

    def _request_shutdown(self, signum: int) -> None:
        if self._triggered:
            return
        self._triggered = True
        try:
            self._signal_name = signal.Signals(signum).name
        except ValueError:
            self._signal_name = str(signum)
        logger.info("shutdown_signal_received signal=%s", self._signal_name)
        self._shutdown_event.set()


async def run_service_until_shutdown(service_factory: Callable[[], Awaitable[None]]) -> None:
    shutdown_manager = ShutdownManager()
    shutdown_manager.install()

    service_task = asyncio.create_task(service_factory(), name="bot-service")
    wait_task = asyncio.create_task(shutdown_manager.wait(), name="shutdown-waiter")

    done, pending = await asyncio.wait(
        {service_task, wait_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    try:
        if wait_task in done and not service_task.done():
            logger.info("shutdown_sequence_started signal=%s", shutdown_manager.signal_name)
            service_task.cancel()

        if service_task in done:
            await service_task
        else:
            await _cancel_task(service_task)
    finally:
        for task in pending:
            await _cancel_task(task)
        await safe_shutdown()


async def safe_shutdown() -> None:
    current_task = asyncio.current_task()
    tasks_to_cancel = [
        task
        for task in asyncio.all_tasks()
        if task is not current_task and not task.done()
    ]

    logger.info("safe_shutdown_started pending_tasks=%s", len(tasks_to_cancel))
    for task in tasks_to_cancel:
        task.cancel()

    if tasks_to_cancel:
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    await get_browser_manager().stop()
    await asyncio.sleep(0.5)
    logger.info("safe_shutdown_finished")


async def _cancel_task(task: asyncio.Task[object]) -> None:
    if task.done():
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
