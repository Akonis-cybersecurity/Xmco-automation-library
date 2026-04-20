import pytest

from xmco_modules import XmcoModule
from xmco_modules.actions.update_yuno_ticket import UpdateYunoTicketAction


@pytest.fixture
def action(module_configuration):
    module = XmcoModule()
    action = UpdateYunoTicketAction(module=module)
    action.module.configuration = module_configuration
    return action


def test_update_ticket_calls_correct_endpoint(action, requests_mock):
    ticket_id = "ticket123"
    etag = "etag_value"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "resolved"},
    )
    result = action.run({"ticket_id": ticket_id, "etag": etag, "status": "resolved"})
    assert result["status"] == "resolved"
    assert f"/yuno/ticket/{ticket_id}" in requests_mock.last_request.path


def test_update_ticket_sends_if_match_header(action, requests_mock):
    ticket_id = "ticket123"
    etag = "my_etag_value"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "in_progress"},
    )
    action.run({"ticket_id": ticket_id, "etag": etag, "status": "in_progress"})
    assert requests_mock.last_request.headers["If-Match"] == etag


def test_update_ticket_fetches_etag_if_not_provided(action, requests_mock):
    ticket_id = "ticket123"
    etag = "auto_etag"
    requests_mock.get(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "_etag": etag, "status": "new"},
    )
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "resolved"},
    )
    action.run({"ticket_id": ticket_id, "status": "resolved"})
    patch_request = [r for r in requests_mock.request_history if r.method == "PATCH"][0]
    assert patch_request.headers["If-Match"] == etag


def test_update_ticket_sends_severity(action, requests_mock):
    ticket_id = "ticket123"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "resolved", "severity": "low"},
    )
    action.run({"ticket_id": ticket_id, "etag": "e1", "status": "resolved", "severity": "low"})
    body = requests_mock.last_request.json()
    assert body["status"] == "resolved"
    assert body["severity"] == "low"


def test_update_ticket_without_severity(action, requests_mock):
    ticket_id = "ticket123"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "in_progress"},
    )
    action.run({"ticket_id": ticket_id, "etag": "e1", "status": "in_progress"})
    body = requests_mock.last_request.json()
    assert "severity" not in body


def test_update_ticket_authorization_header(action, requests_mock):
    ticket_id = "ticket123"
    requests_mock.patch(
        f"https://leportail.xmco.fr/api/yuno/ticket/{ticket_id}",
        json={"_id": ticket_id, "status": "resolved"},
    )
    action.run({"ticket_id": ticket_id, "etag": "e1", "status": "resolved"})
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"
