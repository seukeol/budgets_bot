import aiosqlite
from config import DB_NAME


async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                amount INTEGER,
                descr TEXT
            );
        """)
        await db.commit()



async def create_budget(name):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO budgets (name) VALUES (?)",
            (name, )
        )
        await db.commit()
        return cursor.lastrowid


async def get_budget_id(budget_name):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM budgets WHERE budget_name = ?",
            (budget_name,)
        )
        return await cursor.fetchone()

async def get_budget_balance(budget_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT SUM(amount) FROM transactions WHERE budget_id = ?",
            (budget_id,)
        )
        return await cursor.fetchone()


async def get_all_budgets():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM budgets"
        )
        return await cursor.fetchall()



async def update_budget(budget_id, name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE budgets SET name = ? WHERE id = ?",
            (name, budget_id)
        )
        await db.commit()



async def delete_budget(budget_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM budgets WHERE id = ?",
            (budget_id,)
        )
        await db.commit()


async def create_transaction(budget_id, amount, descr):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO transactions (budget_id, amount, descr) VALUES (?, ?, ?)",
            (budget_id, amount, descr)
        )
        await db.commit()


async def delete_transaction(transaction_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM transactions WHERE transaction_id = ?",
            (transaction_id,)
        )
        await db.commit()


async def get_transaction(transaction_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM budgets WHERE budget_name = ?",
            (transaction_id,)
        )
        return await cursor.fetchone()


async def get_last_transactions(limit=5):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, budget_id, amount, descr FROM transactions "
            "ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return await cursor.fetchall()


async def get_all_transactions():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, budget_id, amount, descr FROM transactions "
            "ORDER BY id ASC"
        )
        return await cursor.fetchall()
