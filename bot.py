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
cur.execute("""CREATE TABLE IF NOT EXISTS u (
    id INTEGER PRIMARY KEY,
    b INTEGER DEFAULT 1000,
    w INTEGER DEFAULT 0,
    l INTEGER DEFAULT 0,
    bet INTEGER DEFAULT 100
)""")
conn.commit()

try:
    cur.execute("ALTER TABLE u ADD COLUMN bet INTEGER DEFAULT 100")
    conn.commit()
except:
    pass

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
        [InlineKeyboardButton(text="⚀ Кости (2 кубика)", callback_data="bones")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="basket")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data="bowl")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="foot")],
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
    await m.answer(
        f"Wasthang Casino\n{m.from_user.first_name}, выбирай игру:",
        reply_markup=menu()
    )

@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer(
        "Команды:\n"
        "/start — меню\n"
        "/balance — баланс\n"
        "/bet СУММА — установить ставку\n"
        "/top — топ игроков\n"
        "--- админ ---\n"
        "/setbal ID СУММА\n"
        "/addbal ID СУММА\n"
        "/reset ID\n"
        "/giveall СУММА"
    )

@dp.message(Command("balance"))
async def mybal(m: types.Message):
    b,_,_,bet = gu(m.from_user.id)
    await m.answer(f"Баланс: {b}\nТекущая ставка: {bet}")

@dp.message(Command("bet"))
async def bet_cmd(m: types.Message):
    try:
        _, amount = m.text.split()
        amt = int(amount)
        if amt < 10:
            await m.answer("Минимум — 10")
            return
        if amt > 1000000:
            await m.answer("Максимум — 1 000 000")
            return
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
        await m.answer(f"✅ Баланс {uid} сброшен до 1000")
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
    await cb.message.answer(f"Текущая ставка: {bet}\nВыбери новую:", reply_markup=bet_menu())
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("setbet_"))
async def setbet_cb(cb: types.CallbackQuery):
    amt = int(cb.data.split("_")[1])
    setbet(cb.from_user.id, amt)
    await cb.answer(f"✅ Ставка: {amt}", show_alert=True)
    await cb.message.answer(f"Ставка установлена: {amt}", reply_markup=menu())

@dp.callback_query(lambda c: c.data=="betmanual")
async def betmanual(cb: types.CallbackQuery):
    await cb.message.answer("Напиши: /bet СУММА\nПример: /bet 250")
    await cb.answer()

# --- БАЗА ---
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
    await cb.message.answer("Выбирай игру:", reply_markup=menu())
    await cb.answer()

# --- СЛОТЫ ---
@dp.callback_query(lambda c: c.data=="slot")
async def slot(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    sym = ["🍒","🍋","🍊","💎","7️⃣"]
    r = [random.choice(sym) for _ in range(3)]
    if r[0]==r[1]==r[2]:
        mult = 10 if r[0]=="💎" else (7 if r[0]=="7️⃣" else 3)
        win = bet*mult
        ub(i, win-bet); stat(i,True)
        t = f"{' | '.join(r)}\n\n🎉 Джекпот! +{win}"
    elif r[0]==r[1] or r[1]==r[2] or r[0]==r[2]:
        win = int(bet*1.5)
        ub(i, win-bet); stat(i,True)
        t = f"{' | '.join(r)}\n\n✅ Совпадение! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"{' | '.join(r)}\n\n❌ Мимо. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Ещё", callback_data="slot")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- РУЛЕТКА ---
@dp.callback_query(lambda c: c.data=="roul")
async def roul(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="r_red")],
        [InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="r_black")],
        [InlineKeyboardButton(text="🟢 Зеро (x14)", callback_data="r_zero")],
    ])
    await cb.message.answer(f"Ставка {bet}. Выбирай цвет:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("r_"))
async def roul_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    num = random.randint(0, 36)
    red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    color = "zero" if num==0 else ("red" if num in red else "black")
    if choice == color:
        win = bet*14 if choice=="zero" else bet*2
        ub(i, win-bet); stat(i,True)
        t = f"Выпало: {num} ({color})\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"Выпало: {num} ({color})\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 Ещё", callback_data="roul")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- КУБИК ---
@dp.callback_query(lambda c: c.data=="dice")
async def dice(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Больше 3 (x2)", callback_data="d_high")],
        [InlineKeyboardButton(text="Меньше 4 (x2)", callback_data="d_low")],
        [InlineKeyboardButton(text="Ровно 6 (x6)", callback_data="d_six")],
    ])
    await cb.message.answer(f"Ставка {bet}. Кубик 1-6:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("d_"))
async def dice_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    dice_msg = await cb.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    num = dice_msg.dice.value
    if choice=="high" and num>3: win,res = bet*2,True
    elif choice=="low" and num<4: win,res = bet*2,True
    elif choice=="six" and num==6: win,res = bet*6,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True)
        t = f"🎲 Выпало: {num}\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"🎲 Выпало: {num}\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Ещё", callback_data="dice")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- МОНЕТКА ---
@dp.callback_query(lambda c: c.data=="coin")
async def coin(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл (x2)", callback_data="c_o")],
        [InlineKeyboardButton(text="🪙 Решка (x2)", callback_data="c_r")],
    ])
    await cb.message.answer(f"Ставка {bet}. Орёл или решка:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("c_"))
async def coin_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    coin_msg = await cb.message.answer_dice(emoji="🎯")
    await asyncio.sleep(2.5)
    val = coin_msg.dice.value
    res = "o" if val % 2 == 1 else "r"
    if choice == res:
        ub(i, bet); stat(i,True)
        t = f"Выпало: {'Орёл' if res=='o' else 'Решка'}\n\n🎉 Победа! +{bet*2}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"Выпало: {'Орёл' if res=='o' else 'Решка'}\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Ещё", callback_data="coin")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- ДАРТС ---
@dp.callback_query(lambda c: c.data=="dart")
async def dart(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 В центр (x5)", callback_data="dt_center")],
        [InlineKeyboardButton(text="🎯 По краю (x2)", callback_data="dt_edge")],
        [InlineKeyboardButton(text="🎯 Мимо (x0.5)", callback_data="dt_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Куда бросаешь?", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("dt_"))
async def dart_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    dart_msg = await cb.message.answer_dice(emoji="🎯")
    await asyncio.sleep(3)
    val = dart_msg.dice.value
    if choice=="center" and val >= 5: win,res = bet*5,True
    elif choice=="edge" and val in [3,4]: win,res = bet*2,True
    elif choice=="miss" and val <= 2: win,res = int(bet*0.5),True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True)
        t = f"🎯 Результат: {val}\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"🎯 Результат: {val}\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Ещё", callback_data="dart")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- БЛЭКДЖЕК ---
@dp.callback_query(lambda c: c.data=="bj")
async def bj(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    player = random.randint(2, 11) + random.randint(2, 11)
    dealer = random.randint(2, 11) + random.randint(2, 11)
    if player > 21:
        ub(i, -bet); stat(i,False)
        t = f"🃏 Ты: {player}\nДилер: {dealer}\n\n💥 Перебор. -{bet}"
    elif dealer > 21:
        ub(i, bet); stat(i,True)
        t = f"🃏 Ты: {player}\nДилер: {dealer}\n\n🎉 У дилера перебор! +{bet*2}"
    elif player > dealer:
        ub(i, bet); stat(i,True)
        t = f"🃏 Ты: {player}\nДилер: {dealer}\n\n🎉 Ты выиграл! +{bet*2}"
    elif player == dealer:
        t = f"🃏 Ты: {player}\nДилер: {dealer}\n\n🤝 Ничья. Ставка возвращена."
    else:
        ub(i, -bet); stat(i,False)
        t = f"🃏 Ты: {player}\nДилер: {dealer}\n\n❌ Дилер выиграл. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Ещё", callback_data="bj")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- КОСТИ (2 кубика) ---
@dp.callback_query(lambda c: c.data=="bones")
async def bones(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сумма >7 (x2)", callback_data="bo_high")],
        [InlineKeyboardButton(text="Сумма <7 (x2)", callback_data="bo_low")],
        [InlineKeyboardButton(text="Ровно 7 (x5)", callback_data="bo_seven")],
        [InlineKeyboardButton(text="Дубль (x8)", callback_data="bo_double")],
    ])
    await cb.message.answer(f"Ставка {bet}. Бросаем 2 кубика:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bo_"))
async def bones_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m1 = await cb.message.answer_dice(emoji="🎲")
    m2 = await cb.message.answer_dice(emoji="🎲")
    await asyncio.sleep(4)
    # Получаем значения (через get_dice или ожидание)
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
        ub(i, win-bet); stat(i,True)
        t = f"Кубики: {v1} и {v2} (сумма {s})\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"Кубики: {v1} и {v2} (сумма {s})\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚀ Ещё", callback_data="bones")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- БАСКЕТБОЛ ---
@dp.callback_query(lambda c: c.data=="basket")
async def basket(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Попаду (x2)", callback_data="bk_hit")],
        [InlineKeyboardButton(text="Точно попаду (x5)", callback_data="bk_sure")],
        [InlineKeyboardButton(text="Промажу (x2)", callback_data="bk_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Бросок в кольцо:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bk_"))
async def basket_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="🏀")
    await asyncio.sleep(3)
    val = m.dice.value  # 1-5 (5 = попал, 1-4 = мимо)
    hit = (val == 5)
    if choice=="hit" and hit: win,res = bet*2,True
    elif choice=="sure" and hit: win,res = bet*5,True
    elif choice=="miss" and not hit: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True)
        t = f"🏀 Бросок: {'попал' if hit else 'мимо'}\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"🏀 Бросок: {'попал' if hit else 'мимо'}\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Ещё", callback_data="basket")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- БОУЛИНГ ---
@dp.callback_query(lambda c: c.data=="bowl")
async def bowl(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Страйк (6) x5", callback_data="bw_strike")],
        [InlineKeyboardButton(text="Сбить 4-5 x3", callback_data="bw_mid")],
        [InlineKeyboardButton(text="Промах (0-2) x2", callback_data="bw_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Бросок шара:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("bw_"))
async def bowl_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="🎳")
    await asyncio.sleep(3)
    val = m.dice.value  # 1-6 (6 = страйк)
    if choice=="strike" and val == 6: win,res = bet*5,True
    elif choice=="mid" and val in [4,5]: win,res = bet*3,True
    elif choice=="miss" and val in [1,2,3]: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True)
        t = f"🎳 Сбито: {val}/6\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"🎳 Сбито: {val}/6\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎳 Ещё", callback_data="bowl")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

# --- ФУТБОЛ ---
@dp.callback_query(lambda c: c.data=="foot")
async def foot(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Гол (4-5) x2", callback_data="ft_goal")],
        [InlineKeyboardButton(text="Штанга (3) x3", callback_data="ft_post")],
        [InlineKeyboardButton(text="Мимо (1-2) x2", callback_data="ft_miss")],
    ])
    await cb.message.answer(f"Ставка {bet}. Удар по воротам:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("ft_"))
async def foot_res(cb: types.CallbackQuery):
    i = cb.from_user.id
    b,_,_,bet = gu(i)
    if b < bet:
        await cb.answer(f"Мало фишек. Нужно {bet}", show_alert=True); return
    choice = cb.data.split("_")[1]
    m = await cb.message.answer_dice(emoji="⚽")
    await asyncio.sleep(3)
    val = m.dice.value  # 1-5
    if choice=="goal" and val in [4,5]: win,res = bet*2,True
    elif choice=="post" and val == 3: win,res = bet*3,True
    elif choice=="miss" and val in [1,2]: win,res = bet*2,True
    else: win,res = 0,False
    if res:
        ub(i, win-bet); stat(i,True)
        t = f"⚽ Удар: {val}\n\n🎉 Победа! +{win}"
    else:
        ub(i, -bet); stat(i,False)
        t = f"⚽ Удар: {val}\n\n❌ Проигрыш. -{bet}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚽ Ещё", callback_data="foot")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
    await cb.message.answer(t, reply_markup=kb)
    await cb.answer()

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
