import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    PreCheckoutQuery,
    WebAppInfo,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn

# Токен вашого бота та посилання на гру вже вписані
BOT_TOKEN = os.getenv("BOT_TOKEN", "8713286143:AAGuB62_ZqOAXMBSmc_J209ieVn_Ef5KDo4")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://incredible-wisp-8ab39d.netlify.app")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceCreateRequest(BaseModel):
    title: str
    description: str
    payload: str
    stars_amount: int


@app.get("/")
def health_check():
    return {"status": "ok", "message": "CyberBerkut backend is running"}


@app.post("/api/create-stars-invoice")
async def create_stars_invoice(req: InvoiceCreateRequest):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload_data = {
        "title": req.title,
        "description": req.description,
        "payload": req.payload,
        "currency": "XTR",
        "prices": [{"label": req.title, "amount": int(req.stars_amount)}],
    }

    resp = requests.post(url, json=payload_data).json()
    if not resp.get("ok"):
        raise HTTPException(
            status_code=400, detail=resp.get("description", "Invoice error")
        )

    return {"invoice_link": resp["result"]}


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text="🦅 Грати", web_app=WebAppInfo(url=WEB_APP_URL)
        ),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ УВІЙТИ В МАТРИЦЮ",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ]
    )

    await message.answer(
        "👋 Вітаємо в системі КІБЕРБЕРКУТ!\n\nТисніть кнопку нижче для запуску гри:",
        reply_markup=keyboard,
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@dp.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(message: types.Message):
    payment = message.successful_payment
    await message.answer(
        f"✅ Оплата {payment.total_amount} ⭐ успішно зарахована!"
    )


async def main():
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), dp.start_polling(bot))


if __name__ == "__main__":
    asyncio.run(main())
