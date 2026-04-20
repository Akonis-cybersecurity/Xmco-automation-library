import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from xmco_modules.triggers.yuno_ticket import YunoTicketConnector


def test_fetch_events_no_cursor(ticket_connector, sample_ticket):
    page1 = {"_items": [sample_ticket]}
    page2 = {"_items": []}
    ticket_connector.client.get_yuno_tickets = MagicMock(side_effect=[page1, page2])

    events, latest_created = ticket_connector.fetch_events()

    assert len(events) == 1
    assert json.loads(events[0])["_id"] == "ticket456"
    assert latest_created == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_fetch_events_with_cursor(ticket_connector, sample_ticket):
    ticket_connector._set_cursor("Wed, 1 Feb 2023 00:00:00 GMT")

    page1 = {"_items": [sample_ticket]}
    page2 = {"_items": []}
    ticket_connector.client.get_yuno_tickets = MagicMock(side_effect=[page1, page2])

    ticket_connector.fetch_events()

    call_kwargs = ticket_connector.client.get_yuno_tickets.call_args_list[0]
    where_arg = call_kwargs[1]["where"]
    assert "_created" in where_arg
    assert where_arg["_created"]["$gt"] == "Wed, 1 Feb 2023 00:00:00 GMT"


def test_fetch_events_pagination(ticket_connector, sample_ticket):
    full_page = {"_items": [sample_ticket] * 50}
    last_page = {"_items": [sample_ticket]}

    ticket_connector.client.get_yuno_tickets = MagicMock(side_effect=[full_page, last_page])

    events, _ = ticket_connector.fetch_events()

    assert len(events) == 51
    assert ticket_connector.client.get_yuno_tickets.call_count == 2


def test_push_events_as_strings(ticket_connector, sample_ticket):
    page1 = {"_items": [sample_ticket]}
    page2 = {"_items": []}
    ticket_connector.client.get_yuno_tickets = MagicMock(side_effect=[page1, page2])

    events, _ = ticket_connector.fetch_events()
    assert all(isinstance(e, str) for e in events)


def test_cursor_updated_after_push(ticket_connector, sample_ticket):
    with patch.object(ticket_connector, "fetch_events", return_value=([json.dumps(sample_ticket)], "Thu, 8 Feb 2023 00:00:00 GMT")):
        with patch.object(ticket_connector, "_stop_event") as mock_stop:
            mock_stop.is_set.side_effect = [False, True]
            with patch("xmco_modules.triggers.yuno_ticket.time.sleep"):
                ticket_connector.run()

    ticket_connector.push_events_to_intakes.assert_called_once()
    assert ticket_connector._get_cursor() == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_cursor_is_most_recent_chronologically_not_alphabetically(ticket_connector):
    # "Thu" > "Mon" alphabetically, but "Mon, 20 Apr 2026" is chronologically later
    items = [
        {"_id": "1", "_created": "Mon, 20 Apr 2026 10:00:00 GMT", "status": "new"},
        {"_id": "2", "_created": "Thu, 17 Apr 2026 08:00:00 GMT", "status": "resolved"},
        {"_id": "3", "_created": "Wed, 19 Apr 2026 15:00:00 GMT", "status": "in_progress"},
    ]
    ticket_connector.client.get_yuno_tickets = MagicMock(
        side_effect=[{"_items": items}, {"_items": []}]
    )

    _, latest_created = ticket_connector.fetch_events()

    assert latest_created == "Mon, 20 Apr 2026 10:00:00 GMT"


def test_no_cursor_no_start_date_uses_30_days_ago(ticket_connector):
    ticket_connector.configuration.start_date = None
    ticket_connector.client.get_yuno_tickets = MagicMock(return_value={"_items": []})

    fixed_now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    with patch("xmco_modules.triggers.yuno_ticket.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        ticket_connector.fetch_events()

    call_kwargs = ticket_connector.client.get_yuno_tickets.call_args[1]
    where = call_kwargs["where"]
    assert "_created" in where
    cursor_used = where["_created"]["$gt"]
    assert "GMT" in cursor_used
    assert "+0000" not in cursor_used
    from email.utils import parsedate_to_datetime
    parsed = parsedate_to_datetime(cursor_used)
    expected = fixed_now - timedelta(days=30)
    assert abs((parsed - expected).total_seconds()) < 5


def test_no_cursor_with_start_date_uses_start_date(ticket_connector):
    ticket_connector.configuration.start_date = "Mon, 01 Jan 2024 00:00:00 GMT"
    ticket_connector.client.get_yuno_tickets = MagicMock(return_value={"_items": []})

    ticket_connector.fetch_events()

    call_kwargs = ticket_connector.client.get_yuno_tickets.call_args[1]
    where = call_kwargs["where"]
    assert where["_created"]["$gt"] == "Mon, 01 Jan 2024 00:00:00 GMT"


def test_existing_cursor_ignores_start_date(ticket_connector):
    ticket_connector.configuration.start_date = "Mon, 01 Jan 2024 00:00:00 GMT"
    ticket_connector._set_cursor("Thu, 8 Feb 2023 00:00:00 GMT")
    ticket_connector.client.get_yuno_tickets = MagicMock(return_value={"_items": []})

    ticket_connector.fetch_events()

    call_kwargs = ticket_connector.client.get_yuno_tickets.call_args[1]
    where = call_kwargs["where"]
    assert where["_created"]["$gt"] == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_authorization_header_in_requests(ticket_connector, requests_mock):
    requests_mock.get(
        "https://leportail.xmco.fr/api/yuno/ticket",
        json={"_items": []},
    )
    ticket_connector.fetch_events()
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key_secret"


def test_run_sleeps_between_cycles(ticket_connector):
    with patch.object(ticket_connector, "fetch_events", return_value=([], None)):
        with patch.object(ticket_connector, "_stop_event") as mock_stop:
            mock_stop.is_set.side_effect = [False, True]
            with patch("xmco_modules.triggers.yuno_ticket.time.sleep") as mock_sleep:
                ticket_connector.run()

    mock_sleep.assert_called_once_with(ticket_connector.configuration.frequency)
