import asyncpg
import os
import logging
from dotenv import load_dotenv

load_dotenv()


class PostgresDB:
    """based from cmyui's {pkg: mysql} but for PostgreSQL on Heroku"""

    @staticmethod
    def dict_factory(row):
        return dict(row)

    def __init__(self):
        self.pool = None

    async def check_database(self):
        query = """
                CREATE TABLE IF NOT EXISTS maps (
                    id SERIAL PRIMARY KEY,
                    set_id BIGINT,
                    artist TEXT,
                    title TEXT,
                    version TEXT,
                    creator TEXT,
                    last_update BIGINT,
                    total_length BIGINT,
                    max_combo BIGINT,
                    status BIGINT,
                    mode BIGINT,
                    bpm REAL,
                    cs REAL,
                    od REAL,
                    ar REAL,
                    hp REAL,
                    star REAL,
                    md5 TEXT
                );

                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    status BIGINT,
                    mapID BIGINT,
                    md5 TEXT NOT NULL,
                    playerID BIGINT NOT NULL,
                    score BIGINT NOT NULL,
                    combo BIGINT NOT NULL,
                    grade TEXT NOT NULL,
                    acc REAL NOT NULL,
                    hit300 BIGINT NOT NULL,
                    hitgeki BIGINT NOT NULL,
                    hit100 BIGINT NOT NULL,
                    hitkatsu BIGINT NOT NULL,
                    hit50 BIGINT NOT NULL,
                    hitmiss BIGINT NOT NULL,
                    mods TEXT,
                    pp REAL DEFAULT 0,
                    date BIGINT DEFAULT 0,
                    local_placement INTEGER DEFAULT 0 NOT NULL,
                    global_placement INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS stats (
                    id SERIAL PRIMARY KEY,
                    pp_rank BIGINT DEFAULT 0,
                    score_rank BIGINT DEFAULT 0,
                    country_pp_rank BIGINT DEFAULT 0,
                    country_score_rank BIGINT DEFAULT 0,
                    pp REAL DEFAULT 0,
                    acc REAL DEFAULT 100.0,
                    tscore BIGINT DEFAULT 0,
                    rscore BIGINT DEFAULT 0,
                    plays BIGINT DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    prefix TEXT,
                    username TEXT,
                    username_safe TEXT,
                    password_hash TEXT,
                    device_id TEXT,
                    sign TEXT,
                    avatar_id TEXT,
                    custom_avatar TEXT,
                    email TEXT,
                    email_hash TEXT,
                    status BIGINT DEFAULT 0,
                    country TEXT
                );

                INSERT INTO users (
                    id, username, username_safe, password_hash, status
                )
                VALUES(-1, '???', '???', 'rembestwaifu69420!!@', -1)
                ON CONFLICT (id) DO NOTHING;

                INSERT INTO stats (id, pp_rank)
                VALUES (-1, 100)
                ON CONFLICT (id) DO NOTHING;
                """
        async with self.pool.acquire() as connection:
            await connection.execute(query)

    async def connect(self):
        # Get the database URL from the environment variable
        database_url = os.getenv("DATABASE_URL")
        self.pool = await asyncpg.create_pool(database_url)
        logging.debug(f"Database connected to: {database_url}")
        await self.check_database()

    async def close(self):
        logging.debug(f"Database closed.")
        await self.pool.close()

    async def execute(self, query: str, params: list = []):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                if "INSERT" in query.upper() and "RETURNING" not in query.upper():
                    query += " RETURNING id"
                logging.debug(f"Executing query: {query} with params: {params}")
                result = await connection.fetchval(query, *params)
        return result

    async def fetch(self, query: str, params: list = [], _all: bool = False):
        async with self.pool.acquire() as connection:
            if _all:
                result = await connection.fetch(query, *params)
            else:
                result = await connection.fetchrow(query, *params)
            logging.debug(f"Fetching query: {query} with params: {params}")
            if not result:
                return None
            return (
                [self.dict_factory(row) for row in result]
                if _all
                else self.dict_factory(result)
            )

    async def fetchall(self, query: str, params: list = []):
        return await self.fetch(query, params, _all=True)

    # Adding context management for easier use
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
