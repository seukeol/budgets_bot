import aiosqlite
from config import DB_NAME


async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS budget (
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


# ---------- READ (все) ----------
async def get_all_budgets():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM budgets"
        )
        return await cursor.fetchall()


# ---------- UPDATE ----------
async def update_budget(budget_id, name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE budgets SET name = ? WHERE id = ?",
            (name, )
        )
        await db.commit()


# ---------- DELETE ----------
async def delete_budget(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        await db.commit()


#