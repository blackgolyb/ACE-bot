from aiogram import F
from src.core.config import get_config


config = get_config()

admin_filter = F.from_user.id.in_(config.bot.admins)

__all__ = [
    "admin_filter"
]
