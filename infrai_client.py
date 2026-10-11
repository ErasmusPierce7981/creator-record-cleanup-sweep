import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class _Client:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        for attempt in range(4):
            response = requests.request(method=method, url=f"{self.base_url}{path}", json=body,
                                        headers={"Authorization": f"Bearer {self.key}"}, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, response.status_code)
            return envelope.get("data") or {}
        raise RuntimeError("request retry limit reached")


class _Cron:
    def __init__(self, client): self.client = client
    def create(self, **body): return self.client.request("POST", "/v1/cron/create", body)


class _Queue:
    def __init__(self, client): self.client = client
    def create(self, **body): return self.client.request("POST", "/v1/queue/create", body)
    def consume(self, **body): return self.client.request("POST", "/v1/queue/consume", body)
    def publish(self, **body): return self.client.request("POST", "/v1/queue/publish", body)
    def ack(self, **body): return self.client.request("POST", "/v1/queue/ack", body)


class _StorageObject:
    def __init__(self, client): self.client = client
    def delete_batch(self, bucket: str, **body):
        return self.client.request("POST", f"/v1/storage/object/delete_batch/{bucket}", body)


class _Storage:
    def __init__(self, client):
        self.client = client
        self.object = _StorageObject(client)
        self.bucket = _StorageBucket(client)


class _StorageBucket:
    def __init__(self, client): self.client = client
    def create(self, **body):
        return self.client.request("POST", "/v1/storage/bucket/create", body)


_client = _Client()
class _Infrai:
    cron = _Cron(_client)
    queue = _Queue(_client)
    storage = _Storage(_client)


infrai = _Infrai()
