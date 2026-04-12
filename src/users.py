# user backend to handle user relationship functions

import falcon
from src.middleware import AuthRequired

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
            
            user = await self.db.create_account(
                form["username"], 
                form["password"],
                form.get("role", "patient"),
                )
            if user is None:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "account with username already exists",
                }
                return
            
            resp.status = falcon.HTTP_201
            resp.media = {"status": "success"}
        
        except:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}

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
                }
        except:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}

# handles fetching user info for current logged in user
class UserApi(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "success", 
            "user": req.context.user
        }

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