import asyncio

import falcon
import falcon.asgi

import src.db as db


class dbMiddle:
    async def process_startup(self, scope, event):
        asyncio.create_task(db.connect())
        print("funny1!")
        await db.connect()


class api:
    async def on_get(self, req, resp):

        resp.status = falcon.HTTP_200
        resp.media = {"server": "is running"}


class usersApi:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        # try:
        users = await self.db.return_users()
        resp.status = falcon.HTTP_200
        resp.media = {"status": "success", "users": users}

    # except:
    # resp.status = falcon.HTTP_500
    # resp.media = {"status": "failure"}


data = db.db_conn(
    host="localhost",
    port="5432",
)

app = falcon.asgi.App(
    middleware=[
        dbMiddle(),
    ],
)
a = api()
users = usersApi(data)

app.add_route("/api/v1", a)
app.add_route("/api/v1/users", users)
