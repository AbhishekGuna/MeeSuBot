import asyncpg
from config import DATABASE_URL

pool = None

async def connect_db():
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10
    )
    print("Database connection pool created.")

async def close_db():
    global pool
    if pool:
        await pool.close()
        print("Database connection pool closed.")

async def execute_query(query, *args):
    global pool
    if not pool:
        raise Exception("Database connection pool is not initialized.")
    
    async with pool.acquire() as connection:
        try:
            result = await connection.fetch(query, *args)
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

