import asyncio
import json
from uuid import UUID

import pyseto


class auth_giver:
    def __init__(self, key):
        self.key = pyseto.Key.new(
            version=3,
            purpose="local",
            key=key,
        )

    def new_refresh_token(self, uid):
        if isinstance(uid, UUID):
            uid = str(uid)
        return pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "refresh_token"}},
            serializer=json,
            exp=604800,
        ).decode()

    def new_token(self, uid):
        if isinstance(uid, UUID):
            uid = str(uid)
        return pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "auth_token"}},
            serializer=json,
            exp=3600,
        ).decode()

    def is_authenticated(self, token):
        try:
            decoded = pyseto.decode(self.key, token, deserializer=json)
            ## TODO: check expired
            return (
                True,
                UUID(decoded.payload["data"]["uid"]),
            )
        except DecryptError as e:
            return (False, None)
        except VerifyError as e:
            return (False, None)
