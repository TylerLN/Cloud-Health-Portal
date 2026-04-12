import asyncio
import json

import aioboto3
import falcon
import falcon.asgi
import pyseto

import src.auth as auth
import src.db as db
import src.users as users
from src.middleware import AuthRequired, authMiddle, dbMiddle

class api:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.media = {"server": "is running"}

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
    host="127.0.0.1",
    port="5432",
)

key = b"FunyKEy"

tokens = auth.auth_giver(key=key)

app = falcon.asgi.App(
    middleware=[
        dbMiddle(data),
        authMiddle(tokens, data),
    ],
)
a = api()
users = users.RegisterApi(data)
login = users.LoginApi(data, tokens)

app.add_route("/api/v1", a)
app.add_route("/api/v1/users/register", users, suffix="register")
app.add_route("/api/v1/login", login)
