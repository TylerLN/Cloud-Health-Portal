import asyncio
import json

from dotenv import load_dotenv
import os

load_dotenv()

import aioboto3
import falcon
import falcon.asgi

import pyseto

import src.auth as auth
import src.db as db
import src.users as users
import src.appointments as appointments
from src.middleware import AuthRequired, authMiddle, dbMiddle

class api:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.media = {"server": "is running"}

# Cross origin resource sharing default blocks requests from one origin to another, so we allow it for frontend and backend, might get rid when terraform connection
class CORSMiddleware:
    async def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', 'http://localhost:5500')
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        resp.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

        if req.method == 'OPTIONS':
            resp.status = falcon.HTTP_200
            resp.complete = True


# we can prob make a separate file for s3filetransfer logic
class patientFiletransferApi(AuthRequired):
    def __init__(self, session):
        self.session = session

    async def on_post(self, req, resp, user_id=None):
        form = await req.get_media()
        async for part in form:
            match (part.name):
                case "file":
                    async with self.session.client("s3") as s3:
                        await s3.upload_fileobj(
                            part.stream, "file-transfers-bucket-cpsc-454", "testkey"
                        )


data = db.db_conn(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

key = b"FunyKEy"
tokens = auth.auth_giver(key=key)

app = falcon.asgi.App(
    middleware=[
        CORSMiddleware(),
        dbMiddle(data),
        authMiddle(tokens, data),
    ],
)

async def handle_500(req, resp, ex, params):
    print(f"Unhandled error: {ex}")
    resp.status = falcon.HTTP_500
    resp.media = {"status": "failure", "message": str(ex)}

app.add_error_handler(Exception, handle_500)

async def handle_options(req, resp):
    resp.status = falcon.HTTP_200

app.add_sink(handle_options, prefix='/api')

# health status
a = api()

register_api = users.RegisterApi(data)
login_api = users.LoginApi(data, tokens)
user_api = users.UserApi(data)
doctor_list_api = users.DoctorListApi(data)
fetch_doctor_api = users.FetchDoctorsAPI(data)
fetch_patient_api = users.FetchPatientsAPI(data)
assign_doctor_api = users.AssignDoctorAPI(data)

appointments_api = appointments.AppointmentsAPI(data)

# routes
app.add_route("/api/v1", a)

app.add_route("/api/v1/users/register", register_api)
app.add_route("/api/v1/users/login", login_api)
app.add_route("/api/v1/users/me", user_api)
app.add_route("/api/v1/users/doctors", doctor_list_api)
app.add_route("/api/v1/users/assigned-doctor", fetch_doctor_api)
app.add_route("/api/v1/users/assigned-patients", fetch_patient_api)
app.add_route("/api/v1/users/assign", assign_doctor_api)

app.add_route("/api/v1/appointments", appointments_api)