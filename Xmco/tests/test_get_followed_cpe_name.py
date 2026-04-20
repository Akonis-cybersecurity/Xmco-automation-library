import pytest

from xmco_modules import XmcoModule
from xmco_modules.actions.get_followed_cpe_name import GetFollowedCpeNameAction


@pytest.fixture
def action(module_configuration):
    module = XmcoModule()
    action = GetFollowedCpeNameAction(module=module)
    action.module.configuration = module_configuration
    return action


def test_get_followed_cpe_names_calls_correct_endpoint(action, requests_mock):
    expected = {"_items": [{"name": "cpe:/a:openssl:openssl"}]}
    requests_mock.get(
        "https://leportail.xmco.fr/api/followed_cpe_name",
        json=expected,
    )
    result = action.run({})
    assert result == expected


def test_get_followed_cpe_names_authorization_header(action, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/followed_cpe_name",
        json={"_items": []},
    )
    action.run({})
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"


def test_get_followed_cpe_names_returns_response(action, requests_mock):
    items = [{"name": "cpe:/a:apache:http_server"}, {"name": "cpe:/a:nginx:nginx"}]
    requests_mock.get(
        "https://leportail.xmco.fr/api/followed_cpe_name",
        json={"_items": items},
    )
    result = action.run({})
    assert result["_items"] == items
