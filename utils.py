from datetime import datetime
import crud



async def create_budget(name, start_balance):
    amount = start_balance

    budget_id = await crud.create_budget(name)

    if amount != 0:
        await crud.create_transaction(
            budget_id,
            amount,
            "start"
        )

    balance = await get_balance(budget_id)

    return budget_id, name, balance


async def edit_budget(budget_id, new_balance):
    budget_balance = await get_balance(budget_id)
    amount = new_balance - budget_balance
    await crud.create_transaction(budget_id, amount,'для обновления баланса')


async def add_expense(budget_id, amount, descr):
    value = amount

    await crud.create_transaction(
        budget_id,
        -value,
        descr
    )

    balance = await get_balance(budget_id)

    return value, balance


async def add_income(budget_id, amount):
    value = amount

    await crud.create_transaction(
        budget_id,
        value,
        ''
    )

    balance = await get_balance(budget_id)

    return value, balance


async def edit_balance(budget_id, new_balance):
    value = new_balance

    current = await get_balance(budget_id)
    delta = value - current

    if delta != 0:
        await crud.create_transaction(
            budget_id,
            delta,
            "manual edit"
        )

    balance = await get_balance(budget_id)

    return balance


async def delete_transaction(transaction_id):
    tx = await crud.get_transaction(transaction_id)

    await crud.delete_transaction(transaction_id)

    balance = await get_balance(tx[1])

    return tx, balance


async def get_balance(budget_id):
    result = await crud.get_budget_balance(budget_id)
    return result[0] if result and result[0] else 0


async def get_budgets():
    return await crud.get_all_budgets()


async def get_last_transactions(limit=10):
    return await crud.get_last_transactions(limit)


async def get_report_data():
    return await crud.get_all_transactions()


