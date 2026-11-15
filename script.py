import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery

# --- НАСТРОЙКИ ---
TOKEN = "9188884978:AAHKqOWsmpVP9GC79kq4km_4rsg3QLleULI"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
users_db = {}

PRICES = {
    "1_month": {"name": "1 месяц", "price": 50},
    "3_months": {"name": "3 месяца", "price": 200},
    "12_months": {"name": "12 месяцев", "price": 500}
}


def get_key_from_file():
    filename = "keys.txt"
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return None
    key = lines[0].strip()
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines[1:])
    return key


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
    ])


def tariffs_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1 месяц — {PRICES['1_month']['price']} ⭐", callback_data="tariff_1_month")],
        [InlineKeyboardButton(text=f"3 месяца — {PRICES['3_months']['price']} ⭐", callback_data="tariff_3_months")],
        [InlineKeyboardButton(text=f"12 месяцев — {PRICES['12_months']['price']} ⭐", callback_data="tariff_12_months")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"purchased_keys": []}
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Добро пожаловать в магазин ключей для Happ VPN.\n"
        "Выбери действие:",
        reply_markup=main_menu()
    )


@dp.callback_query(lambda c: c.data == "buy_key")
async def process_buy(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери тариф:", reply_markup=tariffs_menu())
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("tariff_"))
async def process_tariff(callback: types.CallbackQuery):
    tariff_id = callback.data.replace("tariff_", "")
    tariff = PRICES[tariff_id]

    await callback.message.answer_invoice(
        title=f"VPN ключ на {tariff['name']}",
        description=f"Доступ к Happ VPN на {tariff['name']}",
        payload=f"vpn_{tariff_id}",
        provider_token="",  # Пустая строка для Stars
        currency="XTR",  # XTR — код Telegram Stars
        prices=[LabeledPrice(label="VPN", amount=tariff['price'])]
    )
    await callback.answer()


@dp.pre_checkout_query(lambda query: query.invoice_payload.startswith("vpn_"))
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(lambda message: message.successful_payment is not None)
async def successful_payment(message: types.Message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    tariff_id = payload.replace("vpn_", "")
    tariff = PRICES[tariff_id]

    real_key = get_key_from_file()
    if not real_key:
        await message.answer("❌ Оплата прошла, но ключи закончились. Напишите администратору.")
        return

    if user_id not in users_db:
        users_db[user_id] = {"purchased_keys": []}
    users_db[user_id]["purchased_keys"].append({"key": real_key})

    await message.answer(
        f"✅ Оплата получена!\n\n"
        f"Твой ключ:\n`{real_key}`\n\n"
        f"Скопируй его и вставь в приложение Happ.",
        parse_mode="Markdown"
    )


@dp.callback_query(lambda c: c.data == "profile")
async def process_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_
  data = users_db.get(user_id, {"purchased_keys": []})

    if not user_data["purchased_keys"]:
        text = "У тебя пока нет купленных ключей."
    else:
        text = "Твои ключи:\n\n"
        for item in user_data["purchased_keys"]:
            text += f"• `{item['key']}`\n"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def process_back(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()


async def main():
    print("Бот-магазин запущен и принимает Stars!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
