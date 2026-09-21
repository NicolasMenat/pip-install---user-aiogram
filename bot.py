import asyncio, random, sqlite3, aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8671419411:AAF0-klj1PdMy8Z8oeEBOQDlUh_LZPVzwhQ"
ADMIN_ID = 8684642598
ODDS_API_KEY = "70c105a1bf0fa7a3bdd7bc720040ddd5"  # если пусто — демо-режим

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("casino.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS u (
    id INTEGER PRIMARY KEY,
    b INTEGER DEFAULT 1000,
    w INTEGER DEFAULT 0,
    l INTEGER DEFAULT 0,
    bet INTEGER DEFAULT 100
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    match_id TEXT,
    match_name TEXT,
    outcome TEXT,
    odds REAL,
    stake INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TEXT
)""")
conn.commit()

def gu(i):
    cur.execute("SELECT b,w,l,bet FROM u WHERE id=?", (i,))
    r = cur.fetchone()
    if not r:
        cur.execute("INSERT INTO u (id) VALUES (?)", (i,))
        conn.commit()
        return 1000,0,0,100
    return r

def ub(i,a):
    cur.execute("UPDATE u SET b=b+? WHERE id=?", (a,i))
    conn.commit()

def sb(i,a):
    cur.execute("UPDATE u SET b=? WHERE id=?", (a,i))
    conn.commit()

def setbet(i,a):
    cur.execute("UPDATE u SET bet=? WHERE id=?", (a,i))
    conn.commit()

def stat(i,w):
    if w:
        cur.execute("UPDATE u SET w=w+1 WHERE id=?", (i,))
    else:
        cur.execute("UPDATE u SET l=l+1 WHERE id=?", (i,))
    conn.commit()

def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="slot"),
         InlineKeyboardButton(text="🎡 Рулетка", callback_data="roul")],
        [InlineKeyboardButton(text="🎲 Кубик", callback_data="dice"),
         InlineKeyboardButton(text="🎯 Дартс", callback_data="dart")],
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="coin"),
         InlineKeyboardButton(text="🃏 Блэкджек", callback_data="bj")],
        [InlineKeyboardButton(text="⚀ Кости", callback_data="bones"),
         InlineKeyboardButton(text="🏀 Баскетбол", callback_data="basket")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data="bowl"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data="foot")],
        [InlineKeyboardButton(text="⚽ Ставки на спорт", callback_data="sport")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="bal"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="st")],
        [InlineKeyboardButton(text="🎚 Ставка", callback_data="betmenu")],
    ])

def bet_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="50", callback_data="setbet_50"),
         InlineKeyboardButton(text="100", callback_data="setbet_100")],
        [InlineKeyboardButton(text="500", callback_data="setbet_500"),
         InlineKeyboardButton(text="1000", callback_data="setbet_1000")],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="betmanual")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

@dp.message(Command("start"))
async def s(m: types.Message):
    gu(m.from_user.id)
    await m.answer(f"Wasthang Casino\n{m.from_user.first_name}, выбирай:", reply_markup=menu())

@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer(
        "/start — меню\n"
        "/balance — баланс\n"
        "/bet СУММА — ставка\n"
        "/top — топ\n"
        "/matches — матчи\n"
        "/betmatch НОМЕР ИСХОД СУММА\n"
        "/mybets — мои ставки\n"
        "--- админ ---\n"
        "/setbal ID СУММА\n/addbal ID СУММА\n/reset ID\n/giveall СУММА"
    )

@dp.message(Command("balance"))
async def mybal(m: types.Message):
    b,_,_,bet = gu(m.from_user.id)
    await m.answer(f"Баланс: {b}\nСтавка: {bet}")

@dp.message(Command("bet"))
async def bet_cmd(m: types.Message):
    try:
        _, amount = m.text.split()
        amt = int(amount)
        if amt < 10: 
            await m.answer("Минимум 10"); return
        setbet(m.from_user.id, amt)
        await m.answer(f"✅ Ставка: {amt}")
    except:
        await m.answer("Формат: /bet СУММА")

@dp.message(Command("top"))
async def top(m: types.Message):
    cur.execute("SELECT id, b FROM u ORDER BY b DESC LIMIT 10")
    rows = cur.fetchall()
    t = "🏆 Топ-10:\n\n"
    for idx, (uid, bal) in enumerate(rows, 1):
        t += f"{idx}. ID {uid} — {bal}\n"
    await m.answer(t)

# --- АДМИН ---
@dp.message(Command("setbal"))
async def setbal(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = m.text.split()
        sb(int(uid), int(amount))
        await m.answer(f"✅ Баланс {uid}: {amount}")
    except:
        await m.answer("Формат: /setbal ID СУММА")

@dp.message(Command("addbal"))
async def addbal(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = m.text.split()
        ub(int(uid), int(amount))
        b,_,_,_ = gu(int(uid))
        await m.answer(f"✅ +{amount}. Баланс {uid}: {b}")
    except:
        await m.answer("Формат: /addbal ID СУММА")

@dp.message(Command("reset"))
async def reset(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid = m.text.split()
        sb(int(uid), 1000)
        await m.answer(f"✅ Баланс {uid}: 1000")
    except:
        await m.answer("Формат: /reset ID")

@dp.message(Command("giveall"))
async def giveall(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, amount = m.text.split()
        amt = int(amount)
        cur.execute("UPDATE u SET b=b+?", (amt,))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM u")
        cnt = cur.fetchone()[0]
        await m.answer(f"✅ Всем {cnt} игрокам +{amt}")
    except:
        await m.answer("Формат: /giveall СУММА")

# --- СТАВКА ---
@dp.callback_query(lambda c: c.data=="betmenu")
async def betmenu(cb: types.CallbackQuery):
    _,_,_,bet = gu(cb.from_user.id)
    await cb.message.answer(f"Текущая: {bet}", reply_markup=bet_menu())
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("setbet_"))
async def setbet_cb(cb: types.CallbackQuery):
    amt = int(cb.data.split("_")[1])
    setbet(cb.from_user.id, amt)
    await cb.answer(f"✅ {amt}", show_alert=True)
    await cb.message.answer(f"Ставка: {amt}", reply_markup=menu())

@dp.callback_query(lambda c: c.data=="betmanual")
async def betmanual(cb: types.CallbackQuery):
    await cb.message.answer("Напиши: /bet СУММА")
    await cb.answer()

@dp.callback_query(lambda c: c.data=="bal")
async def bal(cb: types.CallbackQuery):
    b,_,_,bet = gu(cb.from_user.id)
    await cb.answer(f"Баланс: {b}\nСтавка: {bet}", show_alert=True)

@dp.callback_query(lambda c: c.data=="st")
async def st(cb: types.CallbackQuery):
    _,w,l,bet = gu(cb.from_user.id)
    t = w+l
    r = (w/t*100) if t>0 else 0
    await cb.answer(f"Побед: {w}\nПроигрышей: {l}\nВинрейт: {r:.1f}%\nСтавка: {bet}", show_alert=True)

@dp.callback_query(lambda c: c.data=="menu")
async def menu_cb(cb: types.CallbackQuery):
    await cb.message.answer("Выбирай:", reply_markup=menu())
    await cb.answer()

# --- ИГРЫ КАЗИНО ---
@dp.callback_query(lambda c: c.data=="slot")
async def slot(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    sym = ["🍒","🍋","🍊","💎","7️⃣"]
    r = [random.choice(sym) for _ in range(3)]
    if r[0]==r[1]==r[2]:
        mult = 10 if r[0]=="💎" else (7 if r[0]=="7️⃣" else 3)
        win = bet*mult
        ub(i, win-bet); stat(i,True)
        t = f"{' | '.join(r)}\n\n🎉 +{win}"
    elif r[0]==r[1] or r[1]==r[2] or r[0]==r[2]:
        win = int(bet*1.5)
        ub(i, win-bet); stat(i,True)
        t = f"{' | '.join(r)}\n\n✅ +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"{' | '.join(r)}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎰 Ещё", callback_data="slot")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="roul")
async def roul(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="r_red")],
        [InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="r_black")],
        [InlineKeyboardButton(text="🟢 Зеро (x14)", callback_data="r_zero")],
    ])
    await cb.message.answer(f"Ставка {bet}. Цвет:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("r_"))
async def roul_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    num = random.randint(0, 36)
    red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    color = "zero" if num==0 else ("red" if num in red else "black")
    if choice == color:
        win = bet*14 if choice=="zero" else bet*2
        ub(i, win-bet); stat(i,True)
        t = f"Выпало: {num} ({color})\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"Выпало: {num} ({color})\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎡 Ещё", callback_data="roul")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="dice")
async def dice(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Больше 3 (x2)", callback_data="d_high")],
        [InlineKeyboardButton(text="Меньше 4 (x2)", callback_data="d_low")],
        [InlineKeyboardButton(text="Ровно 6 (x6)", callback_data="d_six")],
    ])
    await cb.message.answer(f"Ставка {bet}. Кубик:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("d_"))
async def dice_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    dm = await cb.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    num = dm.dice.value
    if choice=="high" and num>3: win,res = bet*2,True
    elif choice=="low" and num<4: win,res = bet*2,True
    elif choice=="six" and num==6: win,res = bet*6,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"🎲 {num}\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"🎲 {num}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎲 Ещё", callback_data="dice")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="coin")
async def coin(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл (x2)", callback_data="c_o")],
        [InlineKeyboardButton(text="🪙 Решка (x2)", callback_data="c_r")],
    ])
    await cb.message.answer(f"Ставка {bet}. Монетка:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("c_"))
async def coin_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    cm = await cb.message.answer_dice(emoji="🎯")
    await asyncio.sleep(2.5)
    val = cm.dice.value
    res = "o" if val % 2 == 1 else "r"
    if choice == res:
        ub(i, bet); stat(i,True); t = f"{'Орёл' if res=='o' else 'Решка'}\n\n🎉 +{bet*2}"
    else:
        ub(i, -bet); stat(i,False); t = f"{'Орёл' if res=='o' else 'Решка'}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🪙 Ещё", callback_data="coin")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="dart")
async def dart(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В центр (x5)", callback_data="dt_center")],
        [InlineKeyboardButton(text="По краю (x2)", callback_data="dt_edge")],
        [InlineKeyboardButton(text="Мимо (x0.5)", callback_data="dt_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Дротик:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("dt_"))
async def dart_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    dm = await cb.message.answer_dice(emoji="🎯")
    await asyncio.sleep(3)
    val = dm.dice.value
    if choice=="center" and val >= 5: win,res = bet*5,True
    elif choice=="edge" and val in [3,4]: win,res = bet*2,True
    elif choice=="miss" and val <= 2: win,res = int(bet*0.5),True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"🎯 {val}\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"🎯 {val}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎯 Ещё", callback_data="dart")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="bj")
async def bj(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    p = random.randint(2, 11) + random.randint(2, 11)
    d = random.randint(2, 11) + random.randint(2, 11)
    if p > 21:
        ub(i, -bet); stat(i,False); t = f"🃏 Ты: {p}\nДилер: {d}\n\n💥 -{bet}"
    elif d > 21:
        ub(i, bet); stat(i,True); t = f"🃏 Ты: {p}\nДилер: {d}\n\n🎉 +{bet*2}"
    elif p > d:
        ub(i, bet); stat(i,True); t = f"🃏 Ты: {p}\nДилер: {d}\n\n🎉 +{bet*2}"
    elif p == d:
        t = f"🃏 Ты: {p}\nДилер: {d}\n\n🤝 Ничья"
    else:
        ub(i, -bet); stat(i,False); t = f"🃏 Ты: {p}\nДилер: {d}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🃏 Ещё", callback_data="bj")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="bones")
async def bones(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сумма >7 (x2)", callback_data="bo_high")],
        [InlineKeyboardButton(text="Сумма <7 (x2)", callback_data="bo_low")],
        [InlineKeyboardButton(text="Ровно 7 (x5)", callback_data="bo_seven")],
        [InlineKeyboardButton(text="Дубль (x8)", callback_data="bo_double")],
    ])
    await cb.message.answer(f"Ставка {bet}. 2 кубика:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bo_"))
async def bones_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m1 = await cb.message.answer_dice(emoji="🎲")
    m2 = await cb.message.answer_dice(emoji="🎲")
    await asyncio.sleep(4)
    v1 = m1.dice.value if m1.dice else random.randint(1,6)
    v2 = m2.dice.value if m2.dice else random.randint(1,6)
    s = v1 + v2
    dbl = (v1 == v2)
    if choice=="high" and s>7: win,res = bet*2,True
    elif choice=="low" and s<7: win,res = bet*2,True
    elif choice=="seven" and s==7: win,res = bet*5,True
    elif choice=="double" and dbl: win,res = bet*8,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"Кубики: {v1} и {v2} (сумма {s})\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"Кубики: {v1} и {v2} (сумма {s})\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚀ Ещё", callback_data="bones")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="basket")
async def basket(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Попаду (x2)", callback_data="bk_hit")],
        [InlineKeyboardButton(text="Точно (x5)", callback_data="bk_sure")],
        [InlineKeyboardButton(text="Промажу (x2)", callback_data="bk_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Баскетбол:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bk_"))
async def basket_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="🏀")
    await asyncio.sleep(3)
    val = m.dice.value
    hit = (val == 5)
    if choice=="hit" and hit: win,res = bet*2,True
    elif choice=="sure" and hit: win,res = bet*5,True
    elif choice=="miss" and not hit: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"🏀 {'попал' if hit else 'мимо'}\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"🏀 {'попал' if hit else 'мимо'}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏀 Ещё", callback_data="basket")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="bowl")
async def bowl(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Страйк x5", callback_data="bw_strike")],
        [InlineKeyboardButton(text="4-5 x3", callback_data="bw_mid")],
        [InlineKeyboardButton(text="0-2 x2", callback_data="bw_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Боулинг:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bw_"))
async def bowl_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="🎳")
    await asyncio.sleep(3)
    val = m.dice.value
    if choice=="strike" and val==6: win,res = bet*5,True
    elif choice=="mid" and val in [4,5]: win,res = bet*3,True
    elif choice=="miss" and val in [1,2,3]: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"🎳 {val}/6\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"🎳 {val}/6\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎳 Ещё", callback_data="bowl")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data=="foot")
async def foot(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Гол x2", callback_data="ft_goal")],
        [InlineKeyboardButton(text="Штанга x3", callback_data="ft_post")],
        [InlineKeyboardButton(text="Мимо x2", callback_data="ft_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Футбол:", reply_markup=kb); await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("ft_"))
async def foot_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="⚽")
    await asyncio.sleep(3)
    val = m.dice.value
    if choice=="goal" and val in [4,5]: win,res = bet*2,True
    elif choice=="post" and val==3: win,res = bet*3,True
    elif choice=="miss" and val in [1,2]: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True); t = f"⚽ {val}\n\n🎉 +{win}"
    else:
        ub(i, -bet); stat(i,False); t = f"⚽ {val}\n\n❌ -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚽ Ещё", callback_data="foot")],[InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]])
    await cb.message.answer(t, reply_markup=kb); await cb.answer()

# ============ СПОРТ ============
DEMO_MATCHES = [
    {"id": "demo1", "home": "Арсенал", "away": "Челси", "p1": 2.10, "px": 3.40, "p2": 3.20},
    {"id": "demo2", "home": "Реал", "away": "Барселона", "p1": 1.95, "px": 3.60, "p2": 3.80},
    {"id": "demo3", "home": "Бавария", "away": "Боруссия", "p1": 1.70, "px": 3.90, "p2": 4.50},
    {"id": "demo4", "home": "ПСЖ", "away": "Марсель", "p1": 1.55, "px": 4.20, "p2": 5.50},
    {"id": "demo5", "home": "Ювентус", "away": "Интер", "p1": 2.50, "px": 3.10, "p2": 2.80},
]

async def fetch_real_matches():
    if not ODDS_API_KEY:
        return DEMO_MATCHES
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params) as r:
                if r.status != 200:
                    return DEMO_MATCHES
                data = await r.json()
                out = []
                for m in data[:5]:
                    bm = m.get("bookmakers", [])
                    if not bm: continue
                    mk = bm[0]["markets"][0]["outcomes"]
                    if len(mk) < 3: continue
                    out.append({
                        "id": m["id"],
                        "home": m["home_team"],
                        "away": m["away_team"],
                        "p1": mk[0]["price"],
                        "px": mk[1]["price"] if mk[1]["name"]=="Draw" else mk[2]["price"],
                        "p2": mk[-1]["price"],
                    })
                return out or DEMO_MATCHES
    except:
        return DEMO_MATCHES

@dp.callback_query(lambda c: c.data=="sport")
async def sport_cb(cb: types.CallbackQuery):
    matches = await fetch_real_matches()
    text = "⚽ Матчи:\n\n"
    for i, m in enumerate(matches, 1):
        text += f"{i}. {m['home']} vs {m['away']}\n   П1: {m['p1']} | X: {m['px']} | П2: {m['p2']}\n\n"
    text += "Ставь: /betmatch НОМЕР П1/X/П2 СУММА\nПример: /betmatch 1 П1 500"
    await cb.message.answer(text)
    await cb.answer()

@dp.message(Command("matches"))
async def matches_cmd(m: types.Message):
    matches = await fetch_real_matches()
    text = "⚽ Матчи:\n\n"
    for i, mm in enumerate(matches, 1):
        text += f"{i}. {mm['home']} vs {mm['away']}\n   П1: {mm['p1']} | X: {mm['px']} | П2: {mm['p2']}\n\n"
    text += "Ставь: /betmatch НОМЕР П1/X/П2 СУММА"
    await m.answer(text)

@dp.message(Command("betmatch"))
async def betmatch(m: types.Message):
    try:
        parts = m.text.split()
        num = int(parts[1]) - 1
        outcome = parts[2].upper()
        amount = int(parts[3])
    except:
        await m.answer("Формат: /betmatch НОМЕР П1/X/П2 СУММА\nПример: /betmatch 1 П1 500")
        return
    if outcome not in ["П1","X","П2"]:
        await m.answer("Исход: П1, X или П2"); return
    matches = await fetch_real_matches()
    if num < 0 or num >= len(matches):
        await m.answer("Неверный номер матча"); return
    mm = matches[num]
    odds_map = {"П1": mm["p1"], "X": mm["px"], "П2": mm["p2"]}
    odds = odds_map[outcome]
    b,_,_,_ = gu(m.from_user.id)
    if b < amount:
        await m.answer(f"Мало фишек. Баланс: {b}"); return
    ub(m.from_user.id, -amount)
    cur.execute(
        "INSERT INTO bets (user_id, match_id, match_name, outcome, odds, stake, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (m.from_user.id, mm["id"], f"{mm['home']} vs {mm['away']}", outcome, odds, amount, "pending", datetime.now().isoformat())
    )
    conn.commit()
    await m.answer(
        f"✅ Ставка принята:\n"
        f"{mm['home']} vs {mm['away']}\n"
        f"Исход: {outcome} (коэф. {odds})\n"
        f"Ставка: {amount}\n"
        f"Возможный выигрыш: {int(amount*odds)}"
    )

@dp.message(Command("mybets"))
async def mybets(m: types.Message):
    cur.execute("SELECT match_name, outcome, odds, stake, status FROM bets WHERE user_id=? ORDER BY id DESC LIMIT 10", (m.from_user.id,))
    rows = cur.fetchall()
    if not rows:
        await m.answer("У тебя нет ставок"); return
    t = "📋 Твои ставки:\n\n"
    for r in rows:
        t += f"{r[0]}\n{r[1]} × {r[2]} | {r[3]} | {r[4]}\n\n"
    await m.answer(t)

# Автоматический расчёт ставок (раз в 5 минут)
async def settle_bets():
    while True:
        await asyncio.sleep(300)
        cur.execute("SELECT id, user_id, odds, stake FROM bets WHERE status='pending'")
        rows = cur.fetchall()
        for bid, uid, odds, stake in rows:
            # Имитация: 50% шанс победы (в демо-режиме)
            won = random.random() < 0.5
            if won:
                payout = int(stake * odds)
                ub(uid, payout)
                stat(uid, True)
                cur.execute("UPDATE bets SET status='won' WHERE id=?", (bid,))
                try:
                    await bot.send_message(uid, f"🎉 Ставка выиграла! +{payout}")
                except: pass
            else:
                stat(uid, False)
                cur.execute("UPDATE bets SET status='lost' WHERE id=?", (bid,))
                try:
                    await bot.send_message(uid, f"❌ Ставка проиграла. -{stake}")
                except: pass
            conn.commit()

async def main():
    asyncio.create_task(settle_bets())
    await dp.start_polling(bot)

asyncio.run(main())
