from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import crud
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN, valid_ids
from utils import add_expense, add_income, create_budget, get_budgets, get_last_transactions, get_report_data, \
    get_balance, edit_budget
import csv


bot = Bot(token=TOKEN)
dp = Dispatcher()

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Информация о бюджетах", callback_data='budget_infos'),
     InlineKeyboardButton(text="Редактировать бюджет", callback_data='edit_budget')],
    [InlineKeyboardButton(text="➕ Добавить расход", callback_data='add_expense'),
     InlineKeyboardButton(text="💰 Пополнить бюджет", callback_data='refill_budget')],
    [InlineKeyboardButton(text="🆕 Создать новый бюджет", callback_data='create_budget'),
     InlineKeyboardButton(text="❌ Удалить последние транзакции", callback_data='delete_expense')],
    [InlineKeyboardButton(text="📊 Получить таблицу по расходам", callback_data='get_table')],
], resize_keyboard=True)

cancel_kbd = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отмена", callback_data='menu')]
])

back_kbd = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Назад", callback_data='menu')]
])

file_kbd = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Назад", callback_data='menu_from_file')]
])

transactions_kbd = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🗑 Удалить транзакцию", callback_data='delete_transaction')],
    [InlineKeyboardButton(text="◀️ Назад", callback_data='menu')]
])


class DeleteTransaction(StatesGroup):
    waiting_for_id = State()

class AddExpense(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()

class EditBudget(StatesGroup):
    waiting_for_amount = State()

class RefillBudget(StatesGroup):
    waiting_for_amount = State()

class CreateBudget(StatesGroup):
    waiting_for_name = State()
    waiting_for_balance = State()


async def send_notification(message):
    for user in valid_ids:
        await bot.send_message(user, text=message, reply_markup=main_menu)


async def get_budget_buttons(callback_start):
    builder = InlineKeyboardBuilder()
    budgets_info = await get_budgets()
    for budget_info in budgets_info:
        builder.add(InlineKeyboardButton(
            text=f'{budget_info[1]}',
            callback_data=f"{callback_start}_budget_id_{budget_info[0]}"
        ))
    builder.add(
    InlineKeyboardButton(text="❌ Отмена", callback_data='menu'))
    builder.adjust(1)
    kbd = builder.as_markup()
    return kbd


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.from_user.id in valid_ids:
        await message.answer("Главное меню:", reply_markup=main_menu)


@dp.callback_query(F.data == 'menu')
async def main_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id in valid_ids:
        await callback.message.edit_text("Главное меню:", reply_markup=main_menu)

@dp.callback_query(F.data == 'menu_from_file')
async def main_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    if callback.from_user.id in valid_ids:
        await callback.message.answer("Главное меню:", reply_markup=main_menu)


@dp.callback_query(F.data == 'budget_infos')
async def main_handler(callback: CallbackQuery):
    if callback.from_user.id in valid_ids:
        text = ''
        budgets_info = await get_budgets()
        for budget_info in budgets_info:
            budget_balance = await get_balance(budget_info[0])
            text += f"{budget_info[1]}: {budget_balance}р.\n"
        await callback.message.edit_text(text, reply_markup=back_kbd)


@dp.callback_query(F.data == 'add_expense')
async def add_expense_handler(callback: CallbackQuery):
    kbd = await get_budget_buttons('add_expense')
    await callback.message.edit_text("Выберите бюджет для добавления расхода:", reply_markup=kbd)


@dp.callback_query(F.data.startswith('add_expense_budget_id'))
async def select_budget_handler(callback: CallbackQuery, state: FSMContext):
    budget_id = callback.data.split('_')[-1]

    await state.update_data(budget_id=budget_id)

    await state.set_state(AddExpense.waiting_for_amount)

    cancel_kbd = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data='menu')]
    ])

    await callback.message.edit_text(
        "Введите сумму расхода:",
        reply_markup=cancel_kbd
    )


@dp.message(AddExpense.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть положительной. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число. Попробуйте еще раз:")
        return
    await state.update_data(amount=amount)
    await state.set_state(AddExpense.waiting_for_description)
    await message.answer(
        "Введите описание расхода:",
        reply_markup=cancel_kbd
    )


@dp.message(AddExpense.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text
    data = await state.get_data()
    budget_id = data['budget_id']
    amount = data['amount']

    await state.clear()
    await add_expense(budget_id, amount, description)

    text = f"✅ Расход добавлен!\n\n💰 Сумма: {amount}\n 📝 Описание: {description}\n Добавил: {message.from_user.first_name} "
    budget_balance = await get_balance(budget_id)
    text += f"\nНовый баланс: {budget_balance}р.\n"
    await send_notification(text)


@dp.callback_query(F.data == 'refill_budget')
async def refill_budget_handler(callback: CallbackQuery):
    kbd = await get_budget_buttons('refill_budget')
    await callback.message.edit_text("Выберите бюджет для пополнения:", reply_markup=kbd)


@dp.callback_query(F.data.startswith('refill_budget_budget_id'))
async def select_budget_for_refill(callback: CallbackQuery, state: FSMContext):
    budget_id = callback.data.split('_')[-1]
    await state.update_data(budget_id=budget_id)
    await state.set_state(RefillBudget.waiting_for_amount)
    await callback.message.edit_text(
        "Введите сумму пополнения:",
        reply_markup=cancel_kbd
    )

@dp.message(RefillBudget.waiting_for_amount)
async def process_refill_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть положительной. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число. Попробуйте еще раз:")
        return
    data = await state.get_data()
    budget_id = data['budget_id']
    await state.clear()
    await add_income(budget_id, amount)
    text = f"✅ Бюджет пополнен!\n\n💰 Сумма пополнения: {amount}\n Пополнил: {message.from_user.first_name}"
    budget_balance = await get_balance(budget_id)
    text += f"\nНовый баланс: {budget_balance}р.\n"
    await send_notification(text)


@dp.callback_query(F.data == 'create_budget')
async def create_budget_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateBudget.waiting_for_name)
    await callback.message.edit_text(
        "Введите название бюджета:",
        reply_markup=cancel_kbd
    )


@dp.message(CreateBudget.waiting_for_name)
async def process_budget_name(message: types.Message, state: FSMContext):
    budget_name = message.text
    await state.update_data(budget_name=budget_name)
    await state.set_state(CreateBudget.waiting_for_balance)
    await message.answer(
        "Введите стартовый баланс:",
        reply_markup=cancel_kbd
    )


@dp.message(CreateBudget.waiting_for_balance)
async def process_budget_balance(message: types.Message, state: FSMContext):
    try:
        balance = float(message.text.replace(',', '.'))
        if balance < 0:
            await message.answer("Баланс не может быть отрицательным. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число. Попробуйте еще раз:")
        return
    data = await state.get_data()
    budget_name = data['budget_name']
    await state.clear()
    await create_budget(budget_name, balance)
    await message.answer(
        f"✅ Бюджет создан!\n\n"
        f"📝 Название: {budget_name}\n"
        f"💰 Стартовый баланс: {balance}",
        reply_markup=main_menu
    )


@dp.callback_query(F.data == 'delete_expense')
async def show_transactions_handler(callback: CallbackQuery):
    transactions = await get_last_transactions()

    if not transactions:
        await callback.message.edit_text(
            "❌ Нет транзакций для отображения",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data='menu')]
            ])
        )
        return

    text = "📋 Последние транзакции:\n\n"
    for transaction in transactions:
        trans_id, budget_id, amount, descr = transaction
        text += f"🆔 ID: {trans_id}\n💰 Сумма: {amount}\n📝 Описание: {descr}\n\n"

    await callback.message.edit_text(text, reply_markup=transactions_kbd)


@dp.callback_query(F.data == 'delete_transaction')
async def delete_transaction_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteTransaction.waiting_for_id)
    await callback.message.edit_text(
        "Введите ID транзакции для удаления:",
        reply_markup=cancel_kbd
    )


@dp.message(DeleteTransaction.waiting_for_id)
async def process_delete_transaction(message: types.Message, state: FSMContext):
    try:
        transaction_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID (число). Попробуйте еще раз:")
        return

    await state.clear()

    text = f"✅ Транзакция с ID {transaction_id} удалена!\nУдалил: {message.from_user.first_name}"
    await send_notification(text)


@dp.callback_query(F.data == 'get_table')
async def get_table_handler(callback: CallbackQuery):
    transactions = await get_report_data()

    if not transactions:
        await callback.message.edit_text(
            "❌ Нет транзакций для формирования отчета",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data='menu')]
            ])
        )
        return

    filename = "transactions_report.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Budget ID', 'Amount', 'Description'])
        writer.writerows(transactions)

    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📊 Отчет по транзакциям",
        reply_markup=file_kbd
    )
    await callback.message.delete()

async def main():
    await crud.create_tables()
    await dp.start_polling(bot, skip_updates=True)


@dp.callback_query(F.data == 'edit_budget')
async def add_expense_handler(callback: CallbackQuery):
    kbd = await get_budget_buttons('edit_budget')
    await callback.message.edit_text("Выберите бюджет редактирования баланса:", reply_markup=kbd)


@dp.callback_query(F.data.startswith('edit_budget_budget_id'))
async def select_budget_handler(callback: CallbackQuery, state: FSMContext):
    budget_id = callback.data.split('_')[-1]

    await state.update_data(budget_id=budget_id)

    await state.set_state(EditBudget.waiting_for_amount)

    cancel_kbd = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data='menu')]
    ])

    await callback.message.edit_text(
        "Введите новый баланс:",
        reply_markup=cancel_kbd
    )


@dp.message(EditBudget.waiting_for_amount)
async def process_description(message: types.Message, state: FSMContext):
    try:
        balance = float(message.text.replace(',', '.'))
        if balance < 0:
            await message.answer("Баланс не может быть отрицательным. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число. Попробуйте еще раз:")
        return
    data = await state.get_data()
    budget_id = data['budget_id']

    await state.clear()
    await edit_budget(budget_id, balance)

    text = f"✅ Бюджет изменен!\n\n💰 Новый баланс: {balance}\n \n Изменил: {message.from_user.first_name} "
    await send_notification(text)



if __name__ == "__main__":
    asyncio.run(main())