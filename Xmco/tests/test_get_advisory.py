from unittest.mock import MagicMock, patch

import pytest

from xmco_modules import XmcoModule
from xmco_modules.actions.get_advisory import GetAdvisoryAction


@pytest.fixture
def action(module_configuration):
    module = XmcoModule()
    action = GetAdvisoryAction(module=module)
    action.module.configuration = module_configuration
    return action


def test_get_advisory_calls_correct_endpoint(action, requests_mock):
    advisory_id = "abc123"
    expected = {"_id": advisory_id, "severity": "high"}
    requests_mock.get(
        f"https://leportail.xmco.fr/api/advisory/{advisory_id}",
        json=expected,
    )
    result = action.run({"advisory_id": advisory_id})
    assert result == expected


def test_get_advisory_passes_id(action, requests_mock):
    advisory_id = "xyz999"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/advisory/{advisory_id}",
        json={"_id": advisory_id},
    )
    action.run({"advisory_id": advisory_id})
    assert f"/advisory/{advisory_id}" in requests_mock.last_request.path


def test_get_advisory_authorization_header(action, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/advisory/test_id",
        json={"_id": "test_id"},
    )
    action.run({"advisory_id": "test_id"})
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"
