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
import src.files as files

class HealthStatusApi:
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


# health status
a = HealthStatusApi()

register_api = users.RegisterApi(data)
login_api = users.LoginApi(data, tokens)
user_api = users.UserApi(data)
doctor_list_api = users.DoctorListApi(data)
fetch_doctor_api = users.FetchDoctorsAPI(data)
fetch_patient_api = users.FetchPatientsAPI(data)
assign_doctor_api = users.AssignDoctorAPI(data)

appointments_api = appointments.AppointmentsAPI(data)

files_api = files.FilesAPI(data)
file_download_api = files.FileDownloadAPI(data)

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

app.add_route("/api/v1/files", files_api)
app.add_route("/api/v1/files/{file_id}", file_download_api)