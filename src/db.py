#!/usr/bin/env python3
import re
import uuid

import asyncpg


class db_conn:

    def __init__(
        self,
        host: str | list[str] = None,
        port: int | list[int] = None,
        username: str = "postgres",
        password: str = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
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
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database="postgres",
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
            
            # table to hold file info
            await con.execute("""
                CREATE TABLE
                IF NOT EXISTS
                files (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    sender_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    recipient_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    subject TEXT,
                    description TEXT,
                    s3_key TEXT NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT NOW()
                );
            """)

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

    # get current user id for RBAC and frontend purposes, reutrns user_id
    async def get_user_id(self, user_id: uuid.UUID):
        async with self.pool.acquire() as con:
            return await con.fetchrow(
                """
                    SELECT id, username, role
                    FROM accounts 
                    WHERE id = $1;
                """,
                user_id,
            )
    
    # get current user username for doctor registration whitelist method, return username.
    async def get_user_username(self, username: str):
        async with self.pool.acquire() as con:
            return await con.fetchrow(
                """
                    SELECT id, username, role
                    FROM accounts 
                    WHERE username = $1;
                """,
                username,
            )
    
    # change password & update in db
    async def update_password(self, username, new_password):
        async with self.pool.acquire() as con:
            result = await con.fetchval(
                """
                    UPDATE accounts
                    SET password = crypt($2, gen_salt('bf'))
                    WHERE username = $1
                    RETURNING id;
                """,
                username,
                new_password,
            )
        return result
        
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
        
    # get all patients for doctor
    async def get_patients_for_doctor(self, doctor_id):
        async with self.pool.acquire() as con:
            return await con.fetch(
                """
                    SELECT a.id, a.username, a.role
                    FROM doctor_patient dpa
                    JOIN accounts a ON a.id = dpa.patient_id
                    WHERE dpa.doctor_id = $1
                    ORDER BY a.username;
                """,
                doctor_id,
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
                        SELECT a.id, a.doctor_id, a.patient_id, 
                            a.appointment_date, a.appointment_time, 
                            a.reason, a.status,
                            d.username as doctor_name
                        FROM appointments a
                        JOIN accounts d ON d.id = a.doctor_id
                        WHERE a.patient_id = $1
                        AND a.status NOT IN ('completed', 'cancelled')
                        ORDER BY a.appointment_date, a.appointment_time;
                    """,
                    user_id,
                )
            elif role == "doctor":
                return await con.fetch(
                    """
                        SELECT a.id, a.doctor_id, a.patient_id, 
                            a.appointment_date, a.appointment_time, 
                            a.reason, a.status,
                            p.username as patient_name
                        FROM appointments a
                        JOIN accounts p ON p.id = a.patient_id
                        WHERE a.doctor_id = $1
                        AND a.status NOT IN ('completed', 'cancelled')
                        ORDER BY a.appointment_date, a.appointment_time;
                    """,
                    user_id,
                )
            else:
                return None

    # to check if an appointmnet is alr scheduled with the doctor, date, and time, prevent double booking    
    async def appointment_exists(self, doctor_id, appointment_date, appointment_time):
        async with self.pool.acquire() as con:
            return await con.fetchval(
                """
                    SELECT EXISTS (
                        SELECT 1 FROM appointments
                        WHERE doctor_id = $1
                        AND appointment_date = $2
                        AND appointment_time = $3
                        AND status != 'cancelled'
                    );
                """,
                doctor_id,
                appointment_date,
                appointment_time,
            )
        
    # cancel appointment for patients remove the scheduled appoitnment in table
    async def cancel_appointment(self, appointment_id, patient_id):
        async with self.pool.acquire() as con:
            return await con.fetchval(
                """
                    UPDATE appointments
                    SET status = 'cancelled'
                    WHERE id = $1 AND patient_id = $2
                    RETURNING id;
                """,
                appointment_id,
                patient_id,
            )
    
    # complete appointment for doctors, update status to remove
    async def complete_appointment(self, appointment_id, doctor_id):
        async with self.pool.acquire() as con:
            return await con.fetchval(
                """
                    UPDATE appointments
                    SET status = 'completed'
                    WHERE id = $1 AND doctor_id = $2
                    RETURNING id;
                """,
                appointment_id,
                doctor_id,
            )
        
    # DB logic for file transfer feature

    # create and store file info when in s3 bucket
    async def create_file(self, sender_id, recipient_id, filename, subject, description, s3_key):
        async with self.pool.acquire() as con:
            file_id = await con.fetchval(
                """
                    INSERT INTO files(sender_id, recipient_id, filename, subject, description, s3_key)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id;
                """,
                sender_id,
                recipient_id,
                filename,
                subject,
                description,
                s3_key,
            )
        return file_id

    # get all files for current user for inbox
    async def get_all_files(self, user_id):
        async with self.pool.acquire() as con:
            return await con.fetch(
                """
                    SELECT f.id, f.filename, f.subject, f.description, f.s3_key, f.uploaded_at,
                        s.username as sender_name
                    FROM files f
                    JOIN accounts s ON s.id = f.sender_id
                    WHERE f.recipient_id = $1
                    ORDER BY f.uploaded_at DESC;
                """,
                user_id,
            )

    # get specific file by id to generate s3 bucket url for download
    async def get_file(self, file_id, user_id):
        async with self.pool.acquire() as con:
            return await con.fetchrow(
                """
                    SELECT f.id, f.filename, f.s3_key, f.recipient_id, f.sender_id
                    FROM files f
                    WHERE f.id = $1 AND (f.recipient_id = $2 OR f.sender_id = $2);
                """,
                file_id,
                user_id,
            )