import asyncio

import falcon
import falcon.asgi
import pyseto

import src.auth as auth
import src.db as db


class authRequired:
    pass


class dbMiddle:
    def __init__(self, db):
        self.db = db

    async def process_resource(self, req, resp, resource, params):
        if not self.db.connected:
            async with asyncio.TaskGroup() as tg:
                task1 = tg.create_task(self.db.connect())


class authMiddle:
    def __init__(self, auth):
        self.auth = auth

    async def process_resource(self, req, resp, resource, params):
        pass


class api:
    async def on_get(self, req, resp):

        resp.status = falcon.HTTP_200
        resp.media = {"server": "is running"}


class loginApi:
    def __init__(self, db):
        self.db = db

    async def on_post(self, req, resp):
        try:
            form = await req.get_media()
            username = None
            password = None
            async for part in form:
                match (part.name):
                    case "username":
                        username = await part.text
                    case "password":
                        password = await part.text
            if None == username or None == password:
                resp.status = falcon.HTTP_500
                resp.media = {
                    "status": "failure",
                    "message": "please provide username and password",
                    "err": "2",
                }
                return
            login = await self.db.check_password(username, password)
            resp.status = falcon.HTTP_200
            if not login:
                resp.media = {
                    "status": "failure",
                    "message": "username and password pair are not correct",
                    "err": "1",
                }
            else:

                resp.media = {
                    "status": "success",
                }
        except:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}


class usersApi:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        try:
            users = await self.db.return_users()
            resp.status = falcon.HTTP_200
            resp.media = {"status": "success", "users": users}
        except:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}

    async def on_post_register(self, req, resp):
        try:
            form = await req.get_media()
            username = None
            password = None
            async for part in form:
                match (part.name):
                    case "username":
                        username = await part.text
                    case "password":
                        password = await part.text
            if None == username or None == password:
                resp.status = falcon.HTTP_500
                resp.media = {
                    "status": "failure",
                    "message": "please provide username and password",
                    "err": "2",
                }
                return
            users = await self.db.create_account(username, password)
            resp.status = falcon.HTTP_200
            if None == users:
                resp.media = {
                    "status": "failure",
                    "message": "account with username already exists",
                    "err": "1",
                }
            else:
                resp.media = {
                    "status": "success",
                }
        except:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "failure"}


data = db.db_conn(
    host="127.0.0.1",
    port="5432",
)

key = b"FunyKEy"

tokens = auth.auth_giver(key=key)

app = falcon.asgi.App(
    middleware=[
        dbMiddle(data),
        authMiddle(tokens),
    ],
)
a = api()
users = usersApi(data)

app.add_route("/api/v1", a)
app.add_route("/api/v1/users", users)
app.add_route("/api/v1/users/register", users, suffix="register")
