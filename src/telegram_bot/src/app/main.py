from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from fastapi import FastAPI

from app.ai import GeminiClient
from app.config import get_settings
from app.db import init_db
from app.handlers import register_handlers
from app.utils import setup_logging


settings = get_settings()
app = FastAPI(title="AI Nutrition Assistant MVP")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def run_bot() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    setup_logging(settings.log_level)
    init_db()
    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(register_handlers(GeminiClient(settings)))
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
