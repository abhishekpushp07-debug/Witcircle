"""Private platform object storage. All authorization is performed by API callers."""

import os, threading, time
import requests
from functools import lru_cache

BASE = (
    os.environ.get("INTEGRATION_PROXY_URL") or ""
).strip() or "https://integrations.emergentagent.com"
URL = BASE.rstrip("/") + "/objstore/api/v1/storage"
_key = None
_lock = threading.Lock()


class StorageError(Exception):
    pass


def init_storage(force=False):
    global _key
    with _lock:
        if _key and not force:
            return _key
        r = requests.post(
            URL + "/init",
            json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")},
            timeout=30,
        )
        if r.status_code != 200:
            raise StorageError(
                f"Private storage initialization unavailable ({r.status_code}). Check account storage access."
            )
        _key = r.json()["storage_key"]
        return _key


def request(method, path, data=None, content_type=None):
    for attempt in range(3):
        try:
            r = requests.request(
                method,
                URL + "/objects/" + path,
                headers={
                    "X-Storage-Key": init_storage(),
                    "Content-Type": content_type or "application/octet-stream",
                },
                data=data,
                timeout=120,
            )
        except requests.RequestException:
            if attempt == 2:
                raise StorageError(
                    "Private storage connection interrupted. Retry this operation."
                )
            time.sleep(attempt + 1)
            continue
        if r.ok:
            return r
        if r.status_code == 404 and attempt == 0:
            init_storage(force=True)
            continue
        if r.status_code == 503 and attempt < 2:
            time.sleep(attempt + 1)
            continue
        raise StorageError(
            f"Private storage unavailable ({r.status_code}). Retry later or check account storage permissions and quota."
        )
    raise StorageError("Private storage could not complete this request.")


def put_object(path, data, content_type="application/pdf"):
    return request("PUT", path, data, content_type).json()["path"]


@lru_cache(maxsize=8)
def get_object(path):
    return request("GET", path).content
