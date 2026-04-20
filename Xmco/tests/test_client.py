import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from xmco_modules.client import XMCOClient


@pytest.fixture
def client():
    return XMCOClient(api_key="test_key", base_url="https://leportail.xmco.fr/api")


def test_authorization_header_present(client):
    assert "Authorization" in client._session.headers
    assert client._session.headers["Authorization"] == "Bearer test_key"


def test_get_advisories(client, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/advisory",
        json={"_items": [{"_id": "abc", "severity": "high"}]},
    )
    result = client.get_advisories(page=1, max_results=50)
    assert "_items" in result
    assert len(result["_items"]) == 1
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_key"


def test_get_advisories_with_where(client, requests_mock):
    requests_mock.get("https://leportail.xmco.fr/api/advisory", json={"_items": []})
    where = {"_created": {"$gt": "Thu, 8 Feb 2023 00:00:00 GMT"}}
    client.get_advisories(where=where)
    assert "where" in requests_mock.last_request.qs
    parsed = json.loads(requests_mock.last_request.qs["where"][0])
    assert "_created" in parsed
    assert "$gt" in parsed["_created"]
    assert parsed["_created"]["$gt"].lower() == where["_created"]["$gt"].lower()


def test_get_advisory_by_id(client, requests_mock):
    advisory_id = "abc123"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/advisory/{advisory_id}",
        json={"_id": advisory_id, "severity": "urgent"},
    )
    result = client.get_advisory_by_id(advisory_id)
    assert result["_id"] == advisory_id


def test_get_yuno_tickets(client, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/yuno/ticket",
        json={"_items": [{"_id": "t1", "status": "new"}]},
    )
    result = client.get_yuno_tickets()
    assert "_items" in result
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_key"


def test_update_yuno_ticket_sends_if_match(client, requests_mock):
    ticket_id = "ticket123"
    etag = "etag_value"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "resolved"},
    )
    result = client.update_yuno_ticket(ticket_id=ticket_id, etag=etag, data={"status": "resolved"})
    assert requests_mock.last_request.headers["If-Match"] == etag
    assert result["status"] == "resolved"


def test_get_vulnerability(client, requests_mock):
    vuln_id = "vuln001"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/vulnerability/{vuln_id}",
        json={"_id": vuln_id},
    )
    result = client.get_vulnerability(vuln_id)
    assert result["_id"] == vuln_id


def test_get_cve(client, requests_mock):
    cve_id = "CVE-2023-0001"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/cve/{cve_id}",
        json={"_id": cve_id},
    )
    result = client.get_cve(cve_id)
    assert result["_id"] == cve_id


def test_get_followed_cpe_names(client, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/followed_cpe_name",
        json={"_items": [{"name": "cpe:/a:openssl:openssl"}]},
    )
    result = client.get_followed_cpe_names()
    assert "_items" in result


def test_rate_limit_retry(client, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/advisory",
        [
            {"status_code": 429},
            {"json": {"_items": []}, "status_code": 200},
        ],
    )
    with patch("xmco_modules.client.time.sleep") as mock_sleep:
        result = client.get_advisories()
    assert result == {"_items": []}
    mock_sleep.assert_called_once_with(60)


def test_rate_limit_exhaust_retries(client, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/advisory",
        [{"status_code": 429}] * 4,
    )
    with patch("xmco_modules.client.time.sleep"):
        with pytest.raises(requests.HTTPError):
            client.get_advisories()
