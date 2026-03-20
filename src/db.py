#!/usr/bin/env python3
import asyncio
import re
import ssl
import uuid

import asyncpg


class db_conn:

    def __init__(
        self,
        host: str | list[str] = None,
        port: int | list[port] = None,
        username: str = "postgres",
        passfile: str = "./.pgpass",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.passfile = passfile
        self.pool = None

    async def connect(self):
        """
        Creates the connection pool to the database, and creates the required tables if necessary.
        """
        if None != self.pool:
            return

        self.EMAIL_REGEX = re.compile(
            r"^([^@\s\"(),:;<>@+[\]]+)(\+[^@\s\"(),:;<>@+[\]]+)?@([a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+\b)(?!\.)$"
        )

        self.pool = await asyncpg.create_pool(
            dsn="postgres://localhost:5432/postgres?sslmode=verify-ca&sslcert=keys%2Fclient.crt&sslkey=keys%2Fclient.key&sslrootcert=keys%2froot.crt",
            host=self.host,
            port=self.port,
            user=self.username,
            passfile=self.passfile,
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
                        id uuid PRIMARY KEY DEFAULT uuidv7(),
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    );
                """
            )
            await con.execute(
                """
                    CREATE TABLE
                    IF NOT EXISTS
                    personal_info (
                        account_id uuid NOT NULL REFERENCES accounts(id),
                        first_name VARCHAR (255) NOT NULL,
                        middle_name VARCHAR (255),
                        last_name VARCHAR (255)
                    );
                """
            )

    async def account_exists(self, user_email: str) -> bool:
        """
        checks to see if a username has already been used.

        :param user_email: the username of the account to search for.
        :return: a bool representing weather or not the account exists.
        """
        account_exists = False
        async with self.pool.aquire() as con:
            account_exists = await con.fetchval(
                """
                    SELECT exists (SELECT 1 FROM table WHERE username = $1 LIMIT 1);
                """,
                user_email,
            )
        return account_exists

    async def create_account(self, user_email: str, user_password: str) -> int or False:
        """
        Create or update the password of the given user.

        :param user_email: email address of the account to create or update.
        :param user_password: The new password of the account.
        :return: the account id of the created / updated account. Returns False if the account is not created.
        """
        account_id = False
        async with self.pool.acquire() as con:
            account_id = await con.fetchval(
                """
                    INSERT INTO accounts(username,password)
                    VALUES ($1,crypt($2, gen_salt('bf')))
                    ON CONFLICT (username) DO UPDATE
                    SET PASSWORD = crypt($2, gen_salt('bf'))
                    RETURNING NEW.id;
                """,
                user_email,
                user_password,
            )
        return account_id

    async def check_password(self, user_email: str, entered_password: str) -> bool:
        """
        Check to see if the entered username password pair is correct.

        :param user_email: The email of the user to check
        :param entered_password: The candidate password for the given user
        :return: bool representing wether or not the pair is correct or not.
        """
        is_match = False
        async with self.pool.acquire() as con:
            is_match = await con.fetchval(
                """
                    SELECT (password = crypt($2, password))
                    AS pswmatch
                    FROM accounts
                    WHERE username = $1;
                """,
                user_email,
                entered_password,
            )
        return is_match

    async def return_users(self):
        await self.connect()
        resp = {}
        async with self.pool.acquire() as con:
            resp = await con.fetch(
                """
                    SELECT (id, username) from accounts;
                """
            )
        resp = [dict(i) for i in resp]
        resp = [{"id": i["row"][0].hex, "user": i["row"][1]} for i in resp]
        return resp


async def main():
    conn = db_conn(
        host="localhost",
        port="5432",
    )
    await conn.connect()

    account = await conn.create_account("jnellesen@csu.fullerton.edu", "12345")

    print(f"{type(account)} : {account}")
    print(
        f"{isinstance(account, uuid.UUID)} : {uuid.UUID('019d0912-f051-7131-adcd-3d1bc616b622') == account}"
    )

    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "12345")
    print(f"{type(ismatch)} : {ismatch}")
    print(f"is 12345 correct? {'yes' if ismatch else 'no'}")
    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "0")
    print(f"is 0 correct? {'yes' if ismatch else 'no'}")
    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "1")
    print(f"is 1 correct? {'yes' if ismatch else 'no'}")

    ismatch = await conn.check_password("jnellesen@csu.fullerton.invalid", "12345")
    print(f"is 12345 correct with the wrong account? {'yes' if ismatch else 'no'}")


if __name__ == "__main__":
    asyncio.run(main())
