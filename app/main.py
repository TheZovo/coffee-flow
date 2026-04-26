import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.barista_bot import barista_bot, barista_dp
from app.bot import customer_bot, customer_dp
from app.config import settings
from app.database import SessionLocal, engine
from app.migrations import run_startup_migrations
from app.models import Base
from app.routers.admin import router as admin_router
from app.routers.api import router as api_router
from app.routers.web import router as web_router
from app.services.reminders import run_inactive_reminders_once
from app.seed import seed_data

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger("coffeeflow")


async def _start_bot_polling(bot_name: str, dispatcher, bot):
    retry_seconds = max(5, int(settings.TELEGRAM_POLL_RETRY_SECONDS or 20))
    announced_identity = False

    while True:
        try:
            me = await bot.get_me()
            if not announced_identity:
                logger.info("%s bot started as @%s (%s)", bot_name, me.username, me.id)
                announced_identity = True

            await dispatcher.start_polling(
                bot,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
            logger.warning("%s bot polling stopped without exception, restarting in %s seconds", bot_name, retry_seconds)
        except asyncio.CancelledError:
            raise
        except TelegramUnauthorizedError as exc:
            logger.error(
                "%s bot token rejected by Telegram: %s. Polling disabled until restart.",
                bot_name,
                exc,
            )
            return
        except TelegramNetworkError as exc:
            logger.warning(
                "%s bot cannot reach Telegram: %s. Retrying in %s seconds.",
                bot_name,
                exc,
                retry_seconds,
            )
        except Exception as exc:
            logger.exception(
                "%s bot polling stopped with unexpected error: %s. Retrying in %s seconds.",
                bot_name,
                exc,
                retry_seconds,
            )

        await asyncio.sleep(retry_seconds)


async def _run_reminder_scheduler():
    while True:
        try:
            await run_inactive_reminders_once(SessionLocal)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("inactive reminder scheduler failed: %s", exc)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_startup_migrations(conn)

    if settings.AUTO_SEED:
        async with SessionLocal() as session:
            await seed_data(session)

    polling_tasks: list[asyncio.Task] = []
    if settings.CUSTOMER_BOT_ENABLED and customer_bot is not None:
        polling_tasks.append(
            asyncio.create_task(
                _start_bot_polling("customer", customer_dp, customer_bot)
            )
        )
    elif customer_bot is None:
        logger.info("customer bot polling skipped: TELEGRAM_BOT_TOKEN is empty")
    else:
        logger.info("customer bot polling disabled by CUSTOMER_BOT_ENABLED=false")

    if settings.BARISTA_BOT_ENABLED and barista_bot is not None:
        polling_tasks.append(
            asyncio.create_task(
                _start_bot_polling("barista", barista_dp, barista_bot)
            )
        )
    elif barista_bot is None:
        logger.info("barista bot polling skipped: TELEGRAM_BARISTA_BOT_TOKEN is empty")
    else:
        logger.info("barista bot polling disabled by BARISTA_BOT_ENABLED=false")

    reminder_task = asyncio.create_task(_run_reminder_scheduler())

    yield

    for task in polling_tasks:
        task.cancel()
    for task in polling_tasks:
        with suppress(asyncio.CancelledError):
            await task
    reminder_task.cancel()
    with suppress(asyncio.CancelledError):
        await reminder_task

    if customer_bot is not None:
        await customer_bot.session.close()
    if barista_bot is not None:
        await barista_bot.session.close()
    await engine.dispose()


app = FastAPI(
    title="Coffee Flow Mini App",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(web_router)
app.include_router(admin_router)
app.include_router(api_router)
