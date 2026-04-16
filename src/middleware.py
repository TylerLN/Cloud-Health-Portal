import falcon
import asyncio

class AuthRequired:
    pass

class dbMiddle:
    def __init__(self, db):
        self.db = db

    async def process_resource(self, req, resp, resource, params):
        # got rid of task group and just check if db connected, if not wait for it to
        if not self.db.connected:
            await self.db.connect()

class authMiddle: 
    def __init__(self, auth, db):
        self.auth = auth
        self.db = db

    async def process_resource(self, req, resp, resource, params):
        if isinstance(resource, AuthRequired):
            auth_header = req.headers.get("Authorization")            
            
        # check if auth header is present and starts with "Bearer ", if not then unauthenticated
            token = None
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ").strip()
            authenticated, uid = self.auth.is_authenticated(token)
            
            if not authenticated:
                resp.status = falcon.HTTP_403
                resp.media = {"status": "Unauthenticated"}
                resp.complete = True
                return
            
            user = await self.db.get_user_id(uid)
            
            if user is None:
                resp.status = falcon.HTTP_403
                resp.media = {"status": "Unauthenticated"}
                resp.complete = True
                return
            
            req.context.user = dict(user)
            req.context.user_id = uid