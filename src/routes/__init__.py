from aiogram import Router

from .publisher import router as publisher_router


router = Router()

router.include_router(publisher_router)
