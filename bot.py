import asyncio, random, sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8671419411:AAF0-klj1PdMy8Z8oeEBOQDlUh_LZPVzwhQ"
ADMIN_ID = 8684642598

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("casino.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS u (id INTEGER PRIMARY KEY, b INTEGER DEFAULT 1000, w INTEGER DEFAULT 0, l INTEGER DEFAULT 0)")
conn.commit()

def gu(i):
    cur.execute("SELECT b,w,l FROM u WHERE id=?", (i,))
    r = cur.fetchone()
    if not r:
        cur.execute("INSERT INTO u (id) VALUES (?)", (i,))
        conn.commit()
        return 1000,0,0
    return r

def ub(i,a):
    cur.execute("UPDATE u SET b=b+? WHERE id=?", (a,i))
    conn.commit()

def sb(i,a):
    cur.execute("UPDATE u SET b=? WHERE id=?", (a,i))
    conn.commit()

def stat(i,w):
    if w:
        cur.execute("UPDATE u SET w=w+1 WHERE id=?", (i,))
    else:
        cur.execute("UPDATE u SET l=l+1 WHERE id=?", (i,))
    conn.commit()

def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="slot")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="roul")],
        [InlineKeyboardButton(text="🎲 Кубик", callback_data="dice")],
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="bal")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="st")],
    ])

@dp.message(Command("start"))
async def s(m: types.Message):
    gu(m.from_user.id)
    await m.answer(
        f"Wasthang Casino\n{m.from_user.first_name}, ставка: 100 фишек.\nВыбирай игру:",
        reply_markup=menu()
    )

@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer(
        "Команды:\n"
        "/start — меню\n"
        "/balance — твой баланс\n"
        "/top — топ игроков\n"
        "--- админ ---\n"
        "/setbal ID СУММА — установить баланс\n"
        "/addbal ID СУММА — добавить фишки\n"
        "/reset ID — сброс к 1000"
    )

@dp.message(Command("balance"))
async def mybal(m: types.Message):
    b,_,_ = gu(m.from_user.id)
    await m.answer(f"Твой баланс: {b}")

@dp.message(Command("top"))
async def top(m: types.Message):
    cur.execute("SELECT id, b FROM u ORDER BY b DESC LIMIT 10")
    rows = cur.fetchall()
    t = "🏆 Топ-10 игроков:\n\n"
    for idx, (uid, bal) in enumerate(rows, 1):
        t += f"{idx}. ID {uid} — {bal}\n"
    await m.answer(t)

# --- АДМИН-КОМАНДЫ ---

@dp.message(Command("setbal"))
async def setbal(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amount = m.text.split()
        sb(int(uid), int(amount))
        await m.answer(f"✅ Баланс {uid} установлен: {amount}")
    except:
        await m.answer("Формат: /setbal ID СУММА\nПример: /setbal 123456789 50000")

@dp.message(Command("addbal"))
async def addbal(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amount = m.text.split()
        ub(int(uid), int(amount))
        b,_,_ = gu(int(uid))
        await m.answer(f"✅ Добавлено {amount}. Новый баланс {uid}: {b}")
    except:
        await m.answer("Формат: /addbal ID СУММА\nПример: /addbal 123456789 10000")

@dp.message(Command("reset"))
async def reset(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, uid = m.text.split()
        sb(int(uid), 1000)
        await m.answer(f"✅ Баланс {uid} сброшен до 1000")
    except:
        await m.answer("Формат: /reset ID")

@dp.message(Command("giveall"))
async def giveall(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, amount = m.text.split()
        amt = int(amount)
        cur.execute("UPDATE u SET b=b+?", (amt,))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM u")
        cnt = cur.fetchone()[0]
        await m.answer(f"✅ Всем {cnt} игрокам начислено по {amt} фишек")
    except:
        await m.answer("Формат: /giveall СУММА")

# --- ИГРЫ ---

@dp.callback_query(lambda c: c.data=="bal")
async def bal(cb: types.CallbackQuery):
    b,_,_ = gu(cb.from_user.id)
    await cb.answer(f"Баланс: {b}", show_alert=True)

@dp.callback_query(lambda c: c.data=="st")
async def st(cb: types.CallbackQuery):
    _,w,l = gu(cb.from_user.id)
    t = w+l
    r = (w/t*100) if t>0 else 0
    await cb.answer(f"Побед: {w}\nПроигрышей: {l}\nВинрейт: {r:.1f}%", show_alert=True)

@dp.callback_query(lambda c: c.data=="slot")
async def slot(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    sym = ["🍒","🍋","🍊","💎","7️⃣"]
    r = [random.choice(sym) for _ in range(3)]
    if r[0]==r[1]==r[2]:
        win = 1000 if r[0]=="💎" else (700 if r[0]=="7️⃣" else 300)
        ub(i, win-100); stat(i,True)
        t = f"{' | '.join(r)}\n\n🎉 Джекпот! +{win}"
    elif r[0]==r[1] or r[1]==r[2] or r[0]==r[2]:
        ub(i, 50); stat(i,True)
        t = f"{' | '.join(r)}\n\n✅ Совпадение! +150"
    else:
        ub(i, -100); stat(i,False)
        t = f"{' | '.join(r)}\n\n❌ Мимо. -100"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Ещё", callback_data="slot")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data=="roul")
async def roul(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="r_red")],
        [InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="r_black")],
        [InlineKeyboardButton(text="🟢 Зеро (x14)", callback_data="r_zero")],
    ])
    await cb.message.answer("Ставка 100. Выбирай цвет:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("r_"))
async def roul_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    choice = cb.data.split("_")[1]
    num = random.randint(0, 36)
    red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    if num == 0:
        color = "zero"
    elif num in red:
        color = "red"
    else:
        color = "black"
    if choice == color:
        win = 1400 if choice == "zero" else 200
        ub(i, win-100); stat(i,True)
        t = f"Выпало: {num} ({color})\n\n🎉 Победа! +{win}"
    else:
        ub(i, -100); stat(i,False)
        t = f"Выпало: {num} ({color})\n\n❌ Проигрыш. -100"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 Ещё", callback_data="roul")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data=="dice")
async def dice(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Больше 3 (x2)", callback_data="d_high")],
        [InlineKeyboardButton(text="Меньше 4 (x2)", callback_data="d_low")],
        [InlineKeyboardButton(text="Ровно 6 (x6)", callback_data="d_six")],
    ])
    await cb.message.answer("Ставка 100. Кубик 1-6:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("d_"))
async def dice_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    choice = cb.data.split("_")[1]
    num = random.randint(1,6)
    if choice == "high" and num > 3:
        win = 200; res = True
    elif choice == "low" and num < 4:
        win = 200; res = True
    elif choice == "six" and num == 6:
        win = 600; res = True
    else:
        win = 0; res = False
    if res:
        ub(i, win-100); stat(i,True)
        t = f"🎲 Выпало: {num}\n\n🎉 Победа! +{win}"
    else:
        ub(i, -100); stat(i,False)
        t = f"🎲 Выпало: {num}\n\n❌ Проигрыш. -100"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Ещё", callback_data="dice")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data=="coin")
async def coin(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл (x2)", callback_data="c_o")],
        [InlineKeyboardButton(text="🪙 Решка (x2)", callback_data="c_r")],
    ])
    await cb.message.answer("Ставка 100. Орёл или решка:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("c_"))
async def coin_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_ = gu(i)
    if b < 100:
        await cb.answer("Мало фишек", show_alert=True)
        return
    choice = cb.data.split("_")[1]
    res = random.choice(["o","r"])
    if choice == res:
        ub(i, 100); stat(i,True)
        t = f"Выпало: {'Орёл' if res=='o' else 'Решка'}\n\n🎉 Победа! +200"
    else:
        ub(i, -100); stat(i,False)
        t = f"Выпало: {'Орёл' if res=='o' else 'Решка'}\n\n❌ Проигрыш. -100"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Ещё", callback_data="coin")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data=="menu")
async def menu_cb(cb: types.CallbackQuery):
    await cb.message.answer("Выбирай игру:", reply_markup=menu())
    await cb.answer()

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
