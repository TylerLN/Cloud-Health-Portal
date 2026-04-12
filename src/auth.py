import asyncio
import json
from uuid import UUID

import pyseto
from pyseto import DecryptError, VerifyError


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
            ## checks if token is auth token, if it isnt then invalid for authentication
            if decoded.payload["data"]["token_type"] != "auth_token":
                return (False, None)
            ## TODO: check expired
            return (
                True,
                UUID(decoded.payload["data"]["uid"]),
            )
        ## if any errors during decoding, token invalid
        except (DecryptError, VerifyError, KeyError, ValueError, TypeError):
            return (False, None)