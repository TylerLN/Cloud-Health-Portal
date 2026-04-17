# user backend to handle user relationship functions

import falcon
from src.middleware import AuthRequired
import re

# whitelist of doctors and paitnets for demo and autoassign relationship, default doctor is assigned to all patients
WHITELIST = {
    "doctor1@hospital.com" : "doctor",
    "patient1@hospital.com" : "patient",
    "patient2@hospital.com" : "patient",
    "patient3@hospital.com" : "patient"
}

DEFAULT_DOCTOR_USERNAME = "doctor1@hospital.com"

# make password requirements more for better security practice (cap, lower,num, special char)
def is_valid_password(password):
    return(
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\|<>]", password)
    )

# handles user registration (creating account)
class RegisterApi:
    def __init__(self, db):
        self.db = db

    async def on_post(self, req, resp):
        try:
            form = await req.get_media()

            if "username" not in form or "password" not in form:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "please provide username and password",
                }
                return
            
            username = form["username"]
            password = form["password"]

            # the check for valid password w/ helper
            if not is_valid_password(password):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "Password must be at least 8 characters and include uppercase, lowercase, number, and special characters"
                }
                return
            
            # default role if user role not provided.
            role = form.get("role", "patient")

            if username not in WHITELIST:
                resp.status = falcon.HTTP_403
                resp.media = {
                    "status": "failure",
                    "message": "Username not allowed to register",
                }
                return
            
            if role != WHITELIST[username]:
                resp.status = falcon.HTTP_403
                resp.media = {
                    "status": "failure",
                    "message": f"Invalid role for username. Expected role: {WHITELIST[username]}",
                }
                return
            
            user = await self.db.create_account(username, password, role)

            if user is None:
                resp.status = falcon.HTTP_500
                resp.media = {
                    "status": "failure", "message": "account creation failed"
                }
                return
            
            if role == "patient":
                doctor = await self.db.get_user_username(DEFAULT_DOCTOR_USERNAME)
                if doctor is not None:
                    await self.db.assign_doctor_to_patient(doctor["id"], user)

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success"}
            
        except Exception as e:
            print(f"Registration error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure", "message": "internal server error"}
            

# handles user login and creating token
class LoginApi:
    def __init__(self, db, auth):
        self.db = db
        self.auth = auth

    async def on_post(self, req, resp):
        try:
            form = await req.get_media()
            if "username" not in form or "password" not in form:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "please provide username and password",
                    "err": "2",
                }
                return
            login = await self.db.check_password(form["username"], form["password"])
            if None == login or True != login[0]:
                resp.status = falcon.HTTP_401
                resp.media = {
                    "status": "failure",
                    "message": "username and password pair are not correct",
                    "err": "1",
                }
            else:
                resp.status = falcon.HTTP_200
                resp.media = {
                    "status": "success",
                    "refresh": self.auth.new_refresh_token(login[1]),
                    "bearer": self.auth.new_token(login[1]),
                    "role": login[2],
                }
        except Exception as e:
            print(f"Login error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}

# handles fetching user info for current logged in user
class UserApi(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        try:
            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "user": {
                    "id": str(req.context.user["id"]),
                    "username": req.context.user["username"],
                    "role": req.context.user["role"],
                }
            }
        except Exception as e:
            print(f"UserApi error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure", "message": "internal server error"}

# handles fetching doctor info for current logged in user (in case patient has 1+ doctors)
class DoctorListApi(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        doctors = await self.db.get_all_doctors()
        
        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "success", 
            "doctors": [
                {
                    "id": str(d["id"]),
                    "username": d["username"],
                    "role": d["role"],
                }
                for d in doctors
            ],
        }

# handles fetching assigned doctor for current logged in patient
class FetchDoctorsAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        if req.context.user["role"] != "patient":
            resp.status = falcon.HTTP_403
            resp.media = {"status": "failure", "message": "only patients have assigned doctors"}
            return
        doctor = await self.db.get_doctor_for_patient(req.context.user_id)
        if doctor is None:
            resp.status = falcon.HTTP_404
            resp.media = {"status": "failure", "message": "assigned doctor not found"}
        else:
            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success", 
                "doctor": {
                    "id": str(doctor["id"]),
                    "username": doctor["username"],
                    "role": doctor["role"],
                }
            }

# handles fetching assigned patients for current logged in doctor
class FetchPatientsAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        if req.context.user["role"] != "doctor":
            resp.status = falcon.HTTP_403
            resp.media = {"status": "failure", "message": "only doctors have assigned patients"}
            return
        patients = await self.db.get_patients_for_doctor(req.context.user_id)
        if patients is None:
            resp.status = falcon.HTTP_404
            resp.media = {"status": "failure", "message": "assigned patients not found"}
        else:
            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success", 
                "patients": [
                    {
                        "id": str(patient["id"]),
                        "username": patient["username"],
                        "role": patient["role"],
                    }
                    for patient in patients
                ]
            }

# Establish doctor-patient relationship
class AssignDoctorAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_post(self, req, resp):
        if req.context.user["role"] != "doctor":
            resp.status = falcon.HTTP_403
            resp.media = {
                "status": "failure", 
                "message": "only doctors can be assigned to patients",
            }
            return
        
        data = await req.get_media()
        patient_id = data.get("patient_id")

        if not patient_id:
            resp.status = falcon.HTTP_400
            resp.media = {
                "status": "failure", 
                "message": "patient_id is required",
            }
            return
        
        await self.db.assign_doctor_to_patient(
            req.context.user_id, 
            patient_id
        )

        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "success",
            "message": f"Patient {patient_id} assigned to doctor {req.context.user_id}",
        }