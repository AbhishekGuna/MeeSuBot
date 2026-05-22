import asyncpg
import json
from config import DATABASE_URL

pool = None

async def _init_connection(conn):
    """Register JSON/JSONB codecs for every new pool connection."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )

async def connect_db():
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
        init=_init_connection,
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
            result = await connection.fetch(query, *args, timeout=10)
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

