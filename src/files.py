# files.py for file transfer logic, s3 send, receive, inbox, download features

import falcon
import uuid
import aioboto3
from src.middleware import AuthRequired

S3_BUCKET = "files-transfers-bucket-cpsc-454"
AWS_REGION = "us-west-2"

class FilesAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    # get inbox files for current user
    async def on_get(self, req, resp):
        try:
            user_id = req.context.user_id

            files = await self.db.get_all_files(user_id)

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "files": [
                    {
                        "file_id": str(f["id"]),
                        "filename": f["filename"],
                        "subject": f["subject"],
                        "description": f["description"],
                        "sender_name": f["sender_name"],
                        "uploaded_at": str(f["uploaded_at"]),
                    }
                    for f in files
                ],
            }

        except Exception as e:
            print(f"File fetch error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "failure",
                "message": "an error occurred while fetching files",
            }

    # upload file to S3 and store data in db
    async def on_post(self, req, resp):
        try:
            user_id = req.context.user_id
            role = req.context.user["role"]

            form = await req.get_media()

            file_data = None
            filename = None
            subject = None
            description = None
            recipient_id = None

            async for part in form:
                if part.name == "file":
                    filename = part.filename
                    file_data = await part.stream.read()
                elif part.name == "subject":
                    subject = (await part.stream.read()).decode()
                elif part.name == "description":
                    description = (await part.stream.read()).decode()
                elif part.name == "recipient_id":
                    recipient_id = (await part.stream.read()).decode()

            if not file_data or not filename:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "failure",
                    "message": "file is required",
                }
                return

            # if role is patient, send file to doctor,
            if role == "patient":
                doctor = await self.db.get_doctor_for_patient(user_id)
                if not doctor:
                    resp.status = falcon.HTTP_404
                    resp.media = {
                        "status": "failure",
                        "message": "no doctor found for patient",
                    }
                    return
                recipient_id = doctor["id"]
            elif role == "doctor":
                if not recipient_id:
                    resp.status = falcon.HTTP_400
                    resp.media = {
                        "status": "failure",
                        "message": "recipient_id is required for doctor uploads",
                    }
                    return
                recipient_id = uuid.UUID(recipient_id)

            # uupload to s3 in /uploads folder
            s3_key = f"uploads/{user_id}/{recipient_id}/{filename}"

            session = aioboto3.Session()
            async with session.client("s3", region_name=AWS_REGION) as s3:
                await s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=file_data,
                )

            # create the file and store it
            file_id = await self.db.create_file(
                sender_id=user_id,
                recipient_id=recipient_id,
                filename=filename,
                subject=subject,
                description=description,
                s3_key=s3_key,
            )

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "file_id": str(file_id),
            }

        except Exception as e:
            print(f"File upload error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "failure",
                "message": "Error has occured during upload process",
            }

# creating a url for file download.
class FileDownloadAPI(AuthRequired):
    def __init__(self, db):
        self.db = db

    # generate presigned URL for file download
    async def on_get(self, req, resp, file_id):
        try:
            user_id = req.context.user_id

            file = await self.db.get_file(uuid.UUID(file_id), user_id)

            if not file:
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "failure",
                    "message": "file not found",
                }
                return

            # create a presigned url for user to download, expiration time of 1 hr
            session = aioboto3.Session()
            async with session.client("s3", region_name=AWS_REGION) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": S3_BUCKET, "Key": file["s3_key"]},
                    ExpiresIn=3600,
                )

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "download_url": url,
            }

        except Exception as e:
            print(f"File download error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "failure",
                "message": "Error generating link",
            }