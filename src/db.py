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
        self.pool = await asyncpg.create_pool(host=host, port=port, username=username)
        async with self.pool.acquire() as con:
            await con.execute('''
                CREATE TABLE accounts (
                    id serial PRIMARY KEY,
                    name VARCHAR (255) NOT NULL
                )
            ''')

