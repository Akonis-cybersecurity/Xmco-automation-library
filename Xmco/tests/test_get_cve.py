import pytest

from xmco_modules import XmcoModule
from xmco_modules.actions.get_cve import GetCVEAction

BASE = "https://leportail.xmco.fr/api"
MONGO_ID = "5f57713013d93f0052252674"
CVE_NAME = "CVE-2019-6580"


@pytest.fixture
def action(module_configuration):
    module = XmcoModule()
    action = GetCVEAction(module=module)
    action.module.configuration = module_configuration
    return action


# --- MongoDB ID mode ---

def test_get_cve_by_mongo_id_calls_direct_endpoint(action, requests_mock):
    expected = {"_id": MONGO_ID, "cve_id": CVE_NAME, "cvss_score": 9.8}
    requests_mock.get(f"{BASE}/cve/{MONGO_ID}", json=expected)

    result = action.run({"cve_id": MONGO_ID})

    assert result == expected
    assert requests_mock.last_request.path == f"/api/cve/{MONGO_ID}"


def test_get_cve_by_mongo_id_authorization_header(action, requests_mock):
    requests_mock.get(f"{BASE}/cve/{MONGO_ID}", json={"_id": MONGO_ID})

    action.run({"cve_id": MONGO_ID})

    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"


# --- CVE name mode ---

def test_get_cve_by_name_calls_search_endpoint(action, requests_mock):
    cve_doc = {"_id": MONGO_ID, "cve_id": CVE_NAME, "cvss_score": 7.5}
    requests_mock.get(f"{BASE}/cve", json={"_items": [cve_doc]})

    result = action.run({"cve_id": CVE_NAME})

    assert result == cve_doc
    assert requests_mock.last_request.path == "/api/cve"


def test_get_cve_by_name_sends_where_filter(action, requests_mock):
    import json as _json
    from urllib.parse import urlparse, parse_qs

    cve_doc = {"_id": MONGO_ID, "cve_id": CVE_NAME}
    requests_mock.get(f"{BASE}/cve", json={"_items": [cve_doc]})

    action.run({"cve_id": CVE_NAME})

    # Use case-preserving parse of the raw URL
    qs = parse_qs(urlparse(requests_mock.last_request.url).query)
    assert "where" in qs
    where = _json.loads(qs["where"][0])
    assert where == {"cve_id": CVE_NAME}
    assert qs["max_results"] == ["1"]


def test_get_cve_by_name_not_found_raises(action, requests_mock):
    requests_mock.get(f"{BASE}/cve", json={"_items": []})

    with pytest.raises(ValueError, match=CVE_NAME):
        action.run({"cve_id": CVE_NAME})


def test_get_cve_by_name_authorization_header(action, requests_mock):
    requests_mock.get(f"{BASE}/cve", json={"_items": [{"_id": MONGO_ID}]})

    action.run({"cve_id": CVE_NAME})

    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"
