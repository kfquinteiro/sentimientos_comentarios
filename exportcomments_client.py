"""Cliente leve para a API v3 do ExportComments (https://docs.exportcomments.com/)."""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://exportcomments.com/api/v3"
PING_URL = "https://exportcomments.com/api/v1/ping"


class ExportCommentsClient:
    def __init__(self, token=None):
        self.token = token or os.environ["EXPORTCOMMENTS_API_TOKEN"]
        self.headers = {
            "X-AUTH-TOKEN": self.token,
            "Content-Type": "application/json",
        }

    def ping(self):
        response = requests.get(PING_URL, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_job(self, url, options=None):
        payload = {"url": url}
        if options:
            payload["options"] = options
        response = requests.post(f"{BASE_URL}/job", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_job(self, guid):
        response = requests.get(f"{BASE_URL}/job/{guid}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_jobs(self, page=None, limit=None):
        params = {k: v for k, v in {"page": page, "limit": limit}.items() if v is not None}
        response = requests.get(f"{BASE_URL}/jobs", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def wait_for_job(self, guid, poll_seconds=5, timeout_seconds=600):
        elapsed = 0
        while elapsed < timeout_seconds:
            job = self.get_job(guid)
            if job["status"] in ("done", "error"):
                return job
            time.sleep(poll_seconds)
            elapsed += poll_seconds
        raise TimeoutError(f"Job {guid} não finalizou em {timeout_seconds}s")
