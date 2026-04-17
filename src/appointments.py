## appointment logic

import falcon
from src.middleware import AuthRequired

from datetime import date, time

class AppointmentsAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        ## get appointments for user
        try: 
            user_id = req.context.user_id
            role = req.context.user["role"]

            appointments = await self.db.get_appointments(user_id, role)
            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "appointments": [
                    {
                        "appointment_id": str(appointment["id"]),
                        "doctor_id": str(appointment["doctor_id"]),
                        "patient_id": str(appointment["patient_id"]),
                        "appointment_date": str(appointment["appointment_date"]),
                        "appointment_time": str(appointment["appointment_time"]),
                        "reason": appointment["reason"],
                        "status": appointment["status"],
                        "doctor_name": appointment.get("doctor_name"),
                        "patient_name": appointment.get("patient_name"),
                    }
                    for appointment in appointments
                ],
            }

        except Exception as e:
            print(f"Appointment fetch error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "failure",
                "message": "an error occurred while fetching appointments",
            }

    async def on_post(self, req, resp):
        ## create appointment for user
        try:
            user_id = req.context.user_id
            role = req.context.user["role"]

            if role != "patient":
                resp.status = falcon.HTTP_403
                resp.media = {
                    "status": "failure",
                    "message": "only patients can create appointments",
                }
                return

            data = await req.get_media()
            appointment_date = data.get("appointment_date")
            appointment_time = data.get("appointment_time")
            reason = data.get("reason", "")

            # change string to data
            appointment_date = date.fromisoformat(appointment_date)
            appointment_time = time.fromisoformat(appointment_time)

            if not appointment_date or not appointment_time:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "appointment_date and appointment_time are required",
                }
                return

            doctor = await self.db.get_doctor_for_patient(user_id)

            if not doctor:
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "failure",
                    "message": "no doctor found for patient",
                }
                return

            # new check to see if doctor and appointment slot is booked
            already_exists = await self.db.appointment_exists(
                doctor["id"],
                appointment_date,
                appointment_time,
            )

            if already_exists:
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "failure",
                    "message": "That time slot is already booked. Please choose a different time.",
                }
                return
            
            appointment_id = await self.db.create_appointment(
                doctor_id = doctor["id"],
                patient_id = user_id,
                appointment_date = appointment_date,
                appointment_time = appointment_time,
                reason = reason,
            )

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "appointment": {
                    "appointment_id": str(appointment_id),
                    "doctor_id": str(doctor["id"]),
                    "patient_id": str(user_id),
                    "appointment_date": str(appointment_date),
                    "appointment_time": str(appointment_time),
                    "reason": reason,
                },
            }

        except Exception as e:
            print(f"Appointment create error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "failure",
                "message": "an error occurred while creating appointment",
            }