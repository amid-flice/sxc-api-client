import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SxcApiRequestParams:
    method: Callable
    url: str
    payload: dict = field(default_factory=dict)
    auth_required: bool = False
    access_key: str = ""
    secret_key: str = ""

    @property
    def nonce(self) -> int:
        return int(time.time() * 10 ** 6)

    @property
    def headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    @property
    def request_args(self) -> dict:
        payload = self.payload_auth_injected
        return dict(url=self.url, data=json.dumps(payload), headers=self._get_headers_with_auth(payload))

    @property
    def payload_auth_injected(self) -> dict:
        if not self.auth_required:
            return self.payload
        payload = {
            "key": self.access_key,
            "nonce": self.nonce,
            **self.payload
        }
        return payload

    def _get_headers_with_auth(self, payload) -> dict:
        headers = self.headers
        if self.auth_required:
            headers["Hash"] = hmac.new(self.secret_key.encode("utf-8"), json.dumps(payload).encode("utf-8"),
                                       hashlib.sha512).hexdigest()
        return headers

    @property
    def payload_json(self) -> str:
        return json.dumps(self.payload)

    @property
    def payload_auth_injected_json(self) -> str:
        return json.dumps(self.payload_auth_injected)
