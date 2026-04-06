import asyncio
import json

import pyseto


class auth_giver:
    def __init__(self, key):
        self.key = pyseto.Key.new(
            version=3,
            purpose="local",
            key=key,
        )

    def new_refresh_token(self, uid):
        return pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "refresh_token"}},
            serializer=json,
            esp=604800,
        )

    def new_token(self, uid):
        return pyseto.encode(
            self.key,
            {"data": {"uid": uid, "token_type": "auth_token"}},
            serializer=json,
            esp=3600,
        )

    def is_authenticated(self, token):
        try:
            decoded = pyseto.decode(self.key, token, deserializer=json)
            ## TODO: check expired
            return (True, decoded.payload["data"]["uid"])
        except DecryptError as e:
            return (False, None)
        except VerifyError as e:
            return (False, None)
