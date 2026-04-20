import json
import time
from typing import Optional

import requests


class XMCOClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        backoff = 60
        for attempt in range(4):
            response = self._session.get(url, params=params)
            if response.status_code == 429:
                if attempt < 3:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        return {}

    def _patch(self, path: str, etag: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        backoff = 60
        for attempt in range(4):
            response = self._session.patch(url, json=data, headers={"If-Match": etag})
            if response.status_code == 429:
                if attempt < 3:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        return {}

    def get_advisories(self, page: int = 1, max_results: int = 50, where: Optional[dict] = None) -> dict:
        params: dict = {"page": page, "max_results": max_results}
        if where:
            params["where"] = json.dumps(where)
        return self._get("/advisory", params=params)

    def get_advisory_by_id(self, advisory_id: str) -> dict:
        return self._get(f"/advisory/{advisory_id}")

    def get_yuno_tickets(self, page: int = 1, max_results: int = 50, where: Optional[dict] = None) -> dict:
        params: dict = {"page": page, "max_results": max_results}
        if where:
            params["where"] = json.dumps(where)
        return self._get("/yuno/ticket", params=params)

    def get_yuno_ticket_by_id(self, ticket_id: str) -> dict:
        return self._get(f"/yuno/ticket/{ticket_id}")

    def update_yuno_ticket(self, ticket_id: str, etag: str, data: dict) -> dict:
        return self._patch(f"/yuno/ticket/{ticket_id}", etag=etag, data=data)

    def get_vulnerability(self, vuln_id: str) -> dict:
        return self._get(f"/vulnerability/{vuln_id}")

    def get_cve(self, cve_id: str) -> dict:
        return self._get(f"/cve/{cve_id}")

    def get_followed_cpe_names(self) -> dict:
        return self._get("/followed_cpe_name")
