import pytest

from xmco_modules import XmcoModule
from xmco_modules.actions.get_cve import GetCVEAction


@pytest.fixture
def action(module_configuration):
    module = XmcoModule()
    action = GetCVEAction(module=module)
    action.module.configuration = module_configuration
    return action


def test_get_cve_calls_correct_endpoint(action, requests_mock):
    cve_id = "CVE-2023-0001"
    expected = {"_id": cve_id, "cvss_score": 9.8}
    requests_mock.get(
        f"https://leportail.xmco.fr/api/cve/{cve_id}",
        json=expected,
    )
    result = action.run({"cve_id": cve_id})
    assert result == expected


def test_get_cve_passes_id(action, requests_mock):
    cve_id = "CVE-2024-9999"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/cve/{cve_id}",
        json={"_id": cve_id},
    )
    action.run({"cve_id": cve_id})
    assert f"/cve/{cve_id}".lower() in requests_mock.last_request.path.lower()


def test_get_cve_authorization_header(action, requests_mock):
    cve_id = "CVE-2023-0001"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/cve/{cve_id}",
        json={"_id": cve_id},
    )
    action.run({"cve_id": cve_id})
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"
