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
        token = pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "refresh_token"}},
            serializer=json,
            exp=604800,
        )
        return token.decode() if isinstance(token, bytes) else token

    def new_token(self, uid):
        if isinstance(uid, UUID):
            uid = str(uid)
        token = pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "auth_token"}},
            serializer=json,
            exp=3600,
        )
        return token.decode() if isinstance(token, bytes) else token

    def is_authenticated(self, token):
        try:
            print(f"Token received: {token}")
            decoded = pyseto.decode(self.key, token, deserializer=json)
            if decoded.payload["data"]["token_type"] != "auth_token":
                return (False, None)
            return (
                True,
                UUID(decoded.payload["data"]["uid"]),
            )
        except (DecryptError, VerifyError, KeyError, ValueError, TypeError) as e:
            print(f"Auth error: {e}")
            return (False, None)