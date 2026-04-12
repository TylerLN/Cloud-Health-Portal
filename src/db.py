#!/usr/bin/env python3
import asyncio
from pickle import NONE
import re
import ssl
from unittest import result
import uuid

import asyncpg


class db_conn:

    def __init__(
        self,
        host: str | list[str] = None,
        port: int | list[int] = None,
        username: str = "postgres",
        passfile: str = "./.pgpass",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.passfile = passfile
        self.pool = None
        self.connected = False

        self.EMAIL_REGEX = re.compile(
            r"^([^@\s\"(),:;<>@+[\]]+)(\+[^@\s\"(),:;<>@+[\]]+)?@([a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+\b)(?!\.)$"
        )

    async def connect(self):
        """
        Creates the connection pool to the database, and creates the required tables if necessary.
        """
        if self.pool is not None:
            return

        self.pool = await asyncpg.create_pool(
            dsn="postgres://localhost:5432/postgres?sslmode=verify-ca&sslcert=keys%2Fclient.crt&sslkey=keys%2Fclient.key&sslrootcert=keys%2froot.crt",
            host=self.host,
            port=self.port,
            user=self.username,
            passfile=self.passfile,
        )

        self.connected = True

        async with self.pool.acquire() as con:
            await con.execute("""
                    CREATE EXTENSION
                    IF NOT EXISTS
                    pgcrypto;
                """)
            await con.execute("""
                    CREATE TABLE
                    IF NOT EXISTS
                    accounts (
                        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('patient', 'doctor'))
                    );
                """)
            await con.execute("""
                    CREATE TABLE
                    IF NOT EXISTS
                    personal_info (
                        account_id uuid NOT NULL REFERENCES accounts(id),
                        first_name VARCHAR (255) NOT NULL,
                        middle_name VARCHAR (255),
                        last_name VARCHAR (255)
                    );
                """)
            ## table for doctor-patient relationship
            await con.execute("""
                    CREATE TABLE
                    IF NOT EXISTS
                    doctor_patient (
                        doctor_id uuid NOT NULL REFERENCES accounts(id) on DELETE CASCADE,
                        patient_id uuid NOT NULL REFERENCES accounts(id) on DELETE CASCADE,
                        PRIMARY KEY (doctor_id, patient_id)
                    );
                """)
            ## table to store appointments info
            await con.execute("""
                    CREATE TABLE
                    IF NOT EXISTS
                    appointments (
                        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                        doctor_id uuid NOT NULL REFERENCES accounts(id) on DELETE CASCADE,
                        patient_id uuid NOT NULL REFERENCES accounts(id) on DELETE CASCADE,
                        appointment_date DATE NOT NULL,
                        appointment_time TIME NOT NULL,
                        reason TEXT,
                        status TEXT NOT NULL DEFAULT 'scheduled'
                    );
                """)
            
    async def account_exists(self, user_email: str) -> bool:
        """
        checks to see if a username has already been used.

        :param user_email: the username of the account to search for.
        :return: a bool representing weather or not the account exists.
        """
        async with self.pool.acquire() as con:
            account_exists = await con.fetchval(
                """
                    SELECT exists (SELECT 1 FROM accounts WHERE username = $1 LIMIT 1);
                """,
                user_email,
            )
        return account_exists

    async def create_account(self, user_email: str, user_password: str, role: str):
        """
        Create or update the password of the given user.

        :param user_email: email address of the account to create or update.
        :param user_password: The new password of the account.
        :return: the account id of the created / updated account. Returns None if the account is not created.
        """
        # check if email is valid, if not return None
        if not self.EMAIL_REGEX.match(user_email):
            return None
        
        async with self.pool.acquire() as con:
            account_id = await con.fetchval(
                """
                    INSERT INTO accounts(username,password, role)
                    VALUES ($1,crypt($2, gen_salt('bf')), $3)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id;
                """,
                user_email,
                user_password,
                role
            )
        return account_id

    async def check_password(
        self, username: str, password: str):

        """
        Check to see if the entered username password pair is correct.

        :param username: The email of the user to check
        :param password: The candidate password for the given user
        :return: returns None if the username is not associated with an account, or a tuple containing. A bool representing if the password is correct, and the uuid of the account.
        """
        async with self.pool.acquire() as con:
            is_match = await con.fetchrow(
                """
                    SELECT (password = crypt($2, password))
                    AS pswmatch,
                    id,
                    role
                    FROM accounts
                    WHERE username = $1;
                """,
                username,
                password,
            )
        return None if is_match is None else (is_match["pswmatch"], is_match["id"], is_match["role"])
    
    """ 
    functions for appointments & doctor-patient relationships
    """

    # get current user info for RBAC and frontend purposes
    async def get_user_info(self, user_id: uuid.UUID):
        async with self.pool.acquire() as con:
            return await con.fetchrow(
                """
                    SELECT id, username, role
                    FROM accounts 
                    WHERE id = $1;
                """,
                user_id,
            )
        
    # get all doctors in system in the case there are 1+ doctors
    async def get_all_doctors(self):
        async with self.pool.acquire() as con:
            return await con.fetch(
                """
                    SELECT id, username, role
                    FROM accounts 
                    WHERE role = 'doctor'
                    ORDER BY username;
                """,
            )
        
    # creates doctor - patient relationship (doc responsible for patient) puts in table
    async def assign_doctor_to_patient(self, doctor_id: uuid.UUID, patient_id: uuid.UUID):
        async with self.pool.acquire() as con:
            await con.execute(
                """
                    INSERT INTO doctor_patient(doctor_id, patient_id)
                    VALUES ($1, $2)
                    ON CONFLICT (doctor_id, patient_id) DO NOTHING;
                """,
                doctor_id,
                patient_id,
            )

    # check if doctor is assigned to patient for RBAC (if patient assigned to doctor, return true)
    async def doctor_has_patient(self, doctor_id, patient_id) -> bool:
        async with self.pool.acquire() as con:
            return await con.fetchval(
                """
                    SELECT EXISTS (
                        SELECT 1
                        FROM doctor_patient
                        WHERE doctor_id = $1 AND patient_id = $2
                    );
                    """,
                    doctor_id,
                    patient_id,
            )
        
    # get the doctor assigned to this patient for RBAC and frontend stuff
    async def get_doctor_for_patient(self, patient_id):
        async with self.pool.acquire() as con:
            return await con.fetchrow(
                """
                    SELECT a.id, a.username, a.role
                    FROM doctor_patient dpa
                    JOIN accounts a ON a.id = dpa.doctor_id
                    WHERE dpa.patient_id = $1
                    LIMIT 1;
                """,
                patient_id,
            )
        
    # create appointment (for patient role only)
    async def create_appointment(self, doctor_id, patient_id, appointment_date, appointment_time, reason):
        async with self.pool.acquire() as con:
            appointment_id = await con.fetchval(
                """
                    INSERT INTO appointments(doctor_id, patient_id, appointment_date, appointment_time, reason)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id;
                """,
                doctor_id,
                patient_id,
                appointment_date,
                appointment_time,
                reason,
            )
        return appointment_id
    
    # get appointments with RBAC
    async def get_appointments(self, user_id, role):
        async with self.pool.acquire() as con:
            if role == "patient":
                return await con.fetch(
                    """
                        SELECT id, doctor_id, patient_id, appointment_date, appointment_time, reason, status
                        FROM appointments
                        WHERE patient_id = $1
                        ORDER BY appointment_date, appointment_time;
                    """,
                    user_id,
                )
            elif role == "doctor":
                return await con.fetch(
                    """
                        SELECT id, doctor_id, patient_id, appointment_date, appointment_time, reason, status
                        FROM appointments
                        WHERE doctor_id = $1
                        ORDER BY appointment_date, appointment_time;
                    """,
                    user_id,
                )
            else:
                return None


async def main():
    conn = db_conn(
        host="localhost",
        port="5432",
    )
    await conn.connect()

    account = await conn.create_account("jnellesen@csu.fullerton.edu", "12345", "patient")

    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "12345")
    print(f"is 12345 correct? {'yes' if ismatch and ismatch[0] else 'no'}")
    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "0")
    print(f"is 0 correct? {'yes' if ismatch and ismatch[0] else 'no'}")
    ismatch = await conn.check_password("jnellesen@csu.fullerton.edu", "1")
    print(f"is 1 correct? {'yes' if ismatch and ismatch[0] else 'no'}")

    ismatch = await conn.check_password("jnellesen@csu.fullerton.invalid", "12345")
    print(f"is 12345 correct with the wrong account? {'yes' if ismatch and ismatch[0] else 'no'}")


if __name__ == "__main__":
    asyncio.run(main())
