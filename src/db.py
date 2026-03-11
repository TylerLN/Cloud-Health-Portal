import asyncio
import ssl

import asyncpg


class db_conn:

    def __init__(
        self,
        host: str | list[str] = None,
        port: int | list[port] = None,
        username: str = "postgres",
        passfile: str = "./pgpass",
    ):
        self.pool = await asyncpg.create_pool(
            host=host, port=port, username=username, ssl="require"
        )
        async with self.pool.acquire() as con:
            await con.execute(
                """
                    CREATE EXTENSION
                    IF NOT EXISTS
                    pgcrypto;
                """
            )
            await con.execute(
                """
                    CREATE TABLE
                    IF NOT EXISTS
                    accounts (
                        id serial PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                    );
                """
            )
            await con.execute(
                """
                    CREATE TABLE
                    IF NOT EXISTS
                    personal_info (
                        account_id int NOT NULL REFRENCES accounts(id),
                        first_name VARCHAR (255) NOT NULL,
                        middle_name VARCHAR (255),
                        last_name VARCHAR (255)
                    );
                """
            )

    async def 
