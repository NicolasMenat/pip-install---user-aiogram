import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8671419411:AAF0-klj1PdMy8Z8oeEBOQDlUh_LZPVzwhQ"
ADMIN_ID = 8684642598  # твой Telegram ID (узнать у @userinfobot)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- База данных ---
conn = sqlite3.connect("casino.db")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0
)""")
conn.commit()

def get_user(user_id):
    cur.execute("SELECT balance, wins, losses FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return 1000, 0, 0
    return row

def update_balance(user_id, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def add_stat(user_id, win):
    if win:
        cur.execute("UPDATE users SET wins = wins + 1 WHERE user_id=?", (user_id,))
    else:
        cur.execute("UPDATE users SET losses = losses + 1 WHERE user_id=?", (user_id,))
    conn.commit()

# --- Команды ---
@dp.message(Command("start"))
async def start(msg: types.Message):
    get_user(msg.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Крутить слот", callback_data="slot")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
    ])
    await msg.answer(
        f"Добро пожаловать в Wasthang Casino, {msg.from_user.first_name}!\n"
        f"Стартовый баланс: 1000 фишек.\n"
        f"Ставка по умолчанию: 100 фишек.",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "balance")
async def balance(cb: types.CallbackQuery):
    bal, _, _ = get_user(cb.from_user.id)
    await cb.answer(f"Твой баланс: {bal} фишек", show_alert=True)

@dp.callback_query(lambda c: c.data == "stats")
async def stats(cb: types.CallbackQuery):
    _, wins, losses = get_user(cb.from_user.id)
    total = wins + losses
    rate = (wins / total * 100) if total > 0 else 0
    await cb.answer(f"Побед: {wins}\nПроигрышей: {losses}\nВинрейт: {rate:.1f}%", show_alert=True)

@dp.callback_query(lambda c: c.data == "slot")
async def slot(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    bal, _, _ = get_user(user_id)
    bet = 100

    if bal < bet:
        await cb.answer("Недостаточно фишек. Пополни баланс.", show_alert=True)
        return

    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]

    if result[0] == result[1] == result[2]:
        if result[0] == "💎":
            win = bet * 10
        elif result[0] == "7️⃣":
            win = bet * 7
        else:
            win = bet * 3
        update_balance(user_id, win - bet)
        add_stat(user_id, True)
        text = f"{' | '.join(result)}\n\n🎉 ДЖЕКПОТ! Ты выиграл {win} фишек!"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = int(bet * 1.5)
        update_balance(user_id, win - bet)
        add_stat(user_id, True)
        text = f"{' | '.join(result)}\n\n✅ Совпадение! +{win} фишек."
    else:
        update_balance(user_id, -bet)
        add_stat(user_id, False)
        text = f"{' | '.join(result)}\n\n❌ Мимо. -{bet} фишек."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Ещё раз", callback_data="slot")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
    ])
    await cb.message.answer(text, reply_markup=kb)
    await cb.answer()

# --- Админ-команды ---
@dp.message(Command("give"))
async def give(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, target, amount = msg.text.split()
        update_balance(int(target), int(amount))
        await msg.answer(f"Выдано {amount} фишек пользователю {target}")
    except:
        await msg.answer("Формат: /give user_id amount")

@dp.message(Command("broadcast"))
async def broadcast(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    text = msg.text.replace("/broadcast ", "")
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    for u in users:
        try:
            await bot.send_message(u[0], text)
        except:
            pass
    await msg.answer(f"Рассылка отправлена {len(users)} пользователям.")

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
