import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime
import json
import os

from config import BOT_TOKEN, ADMIN_IDS
from workers import WORKERS
from salary import calculate_salary
from storage import save_record, get_all_records, clear_records

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class SalaryForm(StatesGroup):
    choose_worker = State()
    enter_kg = State()
    enter_hours = State()
    choose_point = State()
    enter_sales = State()
    confirm = State()


def make_keyboard(options: list[str], cols: int = 2) -> ReplyKeyboardMarkup:
    rows = []
    for i in range(0, len(options), cols):
        rows.append([KeyboardButton(text=o) for o in options[i:i+cols]])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    names = [w["name"] for w in WORKERS]
    await message.answer(
        "👋 Привіт! Я рахую зарплату.\nОберіть своє ім'я:",
        reply_markup=make_keyboard(names, cols=2)
    )
    await state.set_state(SalaryForm.choose_worker)


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Немає доступу.")
        return
    records = get_all_records()
    if not records:
        await message.answer("📭 Записів ще немає.")
        return

    text = "📊 *Зведення по всіх працівниках:*\n\n"
    total_fund = 0
    by_worker = {}
    for r in records:
        name = r["name"]
        if name not in by_worker:
            by_worker[name] = {"total": 0, "count": 0}
        by_worker[name]["total"] += r["total"]
        by_worker[name]["count"] += 1

    for name, data in sorted(by_worker.items()):
        text += f"👤 *{name}*\n"
        text += f"   Записів: {data['count']}\n"
        text += f"   Сума: {data['total']:.2f} зл\n\n"
        total_fund += data["total"]

    text += f"━━━━━━━━━━━━━━\n💰 *Загальний фонд: {total_fund:.2f} зл*"
    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("admin_clear"))
async def cmd_admin_clear(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Немає доступу.")
        return
    clear_records()
    await message.answer("🗑 Усі записи очищено.")


@dp.message(Command("admin_export"))
async def cmd_admin_export(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Немає доступу.")
        return
    records = get_all_records()
    if not records:
        await message.answer("📭 Немає записів для експорту.")
        return

    lines = ["Ім'я,Дата,Тип,Деталі,База,Відсоток,Премія,Разом"]
    for r in records:
        lines.append(
            f"{r['name']},{r['date']},{r['type']},{r.get('detail','')},{r['base']:.2f},{r.get('percent',0):.2f},{r.get('bonus',0):.2f},{r['total']:.2f}"
        )
    csv_text = "\n".join(lines)

    import io
    buf = io.BytesIO(csv_text.encode("utf-8-sig"))
    buf.name = f"salary_{datetime.now().strftime('%Y%m')}.csv"
    await message.answer_document(types.BufferedInputFile(buf.read(), filename=buf.name))


@dp.message(SalaryForm.choose_worker)
async def process_worker(message: types.Message, state: FSMContext):
    names = [w["name"] for w in WORKERS]
    if message.text not in names:
        await message.answer("Будь ласка, оберіть ім'я зі списку 👇", reply_markup=make_keyboard(names))
        return

    worker = next(w for w in WORKERS if w["name"] == message.text)
    await state.update_data(worker=worker)

    if worker["type"] == "kg":
        await message.answer(
            f"Привіт, {worker['name'].split()[0]}! 👷\nСкільки кілограмів виробили за цей період?",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(SalaryForm.enter_kg)
    else:
        await message.answer(
            f"Привіт, {worker['name'].split()[0]}! 🛒\nСкільки годин відпрацювали?",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(SalaryForm.enter_hours)


@dp.message(SalaryForm.enter_kg)
async def process_kg(message: types.Message, state: FSMContext):
    try:
        kg = float(message.text.replace(",", "."))
        if kg < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введіть коректне число (наприклад: 125.5)")
        return

    await state.update_data(kg=kg)
    data = await state.get_data()
    worker = data["worker"]
    result = calculate_salary(worker, kg=kg)

    text = format_result(result, worker)
    await message.answer(text, parse_mode="Markdown")

    save_record({
        "name": worker["name"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "kg",
        "detail": f"{kg} кг",
        "base": result["base"],
        "bonus": result["bonus"],
        "total": result["total"]
    })

    await state.clear()
    await asyncio.sleep(1)
    names = [w["name"] for w in WORKERS]
    await message.answer("Оберіть ім'я для нового розрахунку:", reply_markup=make_keyboard(names))
    await state.set_state(SalaryForm.choose_worker)


@dp.message(SalaryForm.enter_hours)
async def process_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text.replace(",", "."))
        if hours < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введіть коректне число годин (наприклад: 86)")
        return

    await state.update_data(hours=hours)
    data = await state.get_data()
    worker = data["worker"]

    if worker.get("multi_point"):
        await message.answer(
            "На якій точці ви працювали цього разу?",
            reply_markup=make_keyboard(["A", "B", "C"])
        )
        await state.set_state(SalaryForm.choose_point)
    elif worker.get("threshold"):
        await message.answer("Яка загальна сума продажів за цей період? (зл)")
        await state.set_state(SalaryForm.enter_sales)
    else:
        await finalize_sales(message, state, sales=None)


@dp.message(SalaryForm.choose_point)
async def process_point(message: types.Message, state: FSMContext):
    if message.text not in ["A", "B", "C"]:
        await message.answer("Оберіть точку: A, B або C", reply_markup=make_keyboard(["A", "B", "C"]))
        return

    point = message.text
    threshold = 5000 if point == "A" else 2000
    await state.update_data(point=point, threshold=threshold)
    await message.answer(
        f"Точка {point} ✅\nЯка загальна сума продажів за цей період? (зл)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SalaryForm.enter_sales)


@dp.message(SalaryForm.enter_sales)
async def process_sales(message: types.Message, state: FSMContext):
    try:
        sales = float(message.text.replace(",", ".").replace(" ", ""))
        if sales < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введіть коректну суму (наприклад: 6500)")
        return

    await finalize_sales(message, state, sales=sales)


async def finalize_sales(message, state, sales):
    data = await state.get_data()
    worker = data["worker"]
    hours = data["hours"]

    threshold = data.get("threshold", worker.get("threshold"))
    result = calculate_salary(worker, hours=hours, sales=sales, threshold=threshold)

    text = format_result(result, worker, point=data.get("point"))
    await message.answer(text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

    save_record({
        "name": worker["name"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "sales",
        "detail": f"{hours} год" + (f", {sales} зл" if sales else ""),
        "base": result["base"],
        "percent": result.get("percent", 0),
        "bonus": result["bonus"],
        "total": result["total"]
    })

    await state.clear()
    await asyncio.sleep(1)
    names = [w["name"] for w in WORKERS]
    await message.answer("Оберіть ім'я для нового розрахунку:", reply_markup=make_keyboard(names))
    await state.set_state(SalaryForm.choose_worker)


def format_result(result, worker, point=None):
    lines = [f"✅ *Розрахунок для {worker['name']}*\n"]
    if worker["type"] == "kg":
        lines.append(f"📦 Виробництво: {result['kg']} кг × 9 зл = *{result['base']:.2f} зл*")
        if result.get("fixed_extra", 0) > 0:
            lines.append(f"➕ Надбавка: *+{result['fixed_extra']:.2f} зл*")
    else:
        pt = f" (точка {point})" if point else ""
        lines.append(f"🕐 Погодинна{pt}: {result['hours']} год × {worker['rate']} зл = *{result['base']:.2f} зл*")
        if result.get("percent", 0) > 0:
            lines.append(f"📈 2% від понад порогу: *+{result['percent']:.2f} зл*")

    if result.get("bonus", 0) > 0:
        lines.append(f"🎁 Стала премія: *+{result['bonus']:.2f} зл*")

    lines.append(f"\n💰 *Разом: {result['total']:.2f} зл*")
    lines.append(f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
