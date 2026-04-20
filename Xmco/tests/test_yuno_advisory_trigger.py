import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from xmco_modules.triggers.yuno_advisory import YunoAdvisoryConnector


def test_fetch_events_no_cursor(advisory_connector, sample_advisory):
    page1 = {"_items": [sample_advisory]}
    page2 = {"_items": []}
    advisory_connector.client.get_advisories = MagicMock(side_effect=[page1, page2])

    events, latest_created = advisory_connector.fetch_events()

    assert len(events) == 1
    assert json.loads(events[0])["_id"] == "abc123"
    assert latest_created == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_fetch_events_with_cursor(advisory_connector, sample_advisory):
    advisory_connector._set_cursor("Wed, 1 Feb 2023 00:00:00 GMT")

    page1 = {"_items": [sample_advisory]}
    page2 = {"_items": []}
    advisory_connector.client.get_advisories = MagicMock(side_effect=[page1, page2])

    advisory_connector.fetch_events()

    call_kwargs = advisory_connector.client.get_advisories.call_args_list[0]
    where_arg = call_kwargs[1]["where"]
    assert "_created" in where_arg
    assert where_arg["_created"]["$gt"] == "Wed, 1 Feb 2023 00:00:00 GMT"


def test_fetch_events_pagination(advisory_connector):
    item_base = {"_id": "x", "severity": "low", "_created": "Thu, 8 Feb 2023 00:00:00 GMT"}
    full_page = {"_items": [item_base] * 50}
    last_page = {"_items": [item_base]}

    advisory_connector.client.get_advisories = MagicMock(side_effect=[full_page, last_page])

    events, _ = advisory_connector.fetch_events()

    assert len(events) == 51
    assert advisory_connector.client.get_advisories.call_count == 2


def test_push_events_as_strings(advisory_connector, sample_advisory):
    page1 = {"_items": [sample_advisory]}
    page2 = {"_items": []}
    advisory_connector.client.get_advisories = MagicMock(side_effect=[page1, page2])

    events, _ = advisory_connector.fetch_events()
    assert all(isinstance(e, str) for e in events)
    assert json.loads(events[0]) == sample_advisory


def test_cursor_updated_after_push(advisory_connector, sample_advisory):
    page1 = {"_items": [sample_advisory]}
    page2 = {"_items": []}

    with patch.object(advisory_connector, "fetch_events", return_value=([json.dumps(sample_advisory)], "Thu, 8 Feb 2023 00:00:00 GMT")):
        with patch.object(advisory_connector, "_stop_event") as mock_stop:
            mock_stop.is_set.side_effect = [False, True]
            with patch("xmco_modules.triggers.yuno_advisory.time.sleep"):
                advisory_connector.run()

    advisory_connector.push_events_to_intakes.assert_called_once()
    assert advisory_connector._get_cursor() == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_min_severity_filter(advisory_connector):
    advisory_connector.configuration.min_severity = "high"
    where = advisory_connector._build_where(None)
    assert "severity" in where
    assert set(where["severity"]["$in"]) == {"high", "urgent"}


def test_min_severity_low_includes_all(advisory_connector):
    advisory_connector.configuration.min_severity = "low"
    where = advisory_connector._build_where(None)
    assert set(where["severity"]["$in"]) == {"low", "medium", "high", "urgent"}


def test_cursor_is_most_recent_chronologically_not_alphabetically(advisory_connector):
    # "Thu" > "Mon" alphabetically, but "Mon, 20 Apr 2026" is chronologically later
    items = [
        {"_id": "1", "_created": "Mon, 20 Apr 2026 10:00:00 GMT", "severity": "high"},
        {"_id": "2", "_created": "Thu, 17 Apr 2026 08:00:00 GMT", "severity": "low"},
        {"_id": "3", "_created": "Wed, 19 Apr 2026 15:00:00 GMT", "severity": "medium"},
    ]
    advisory_connector.client.get_advisories = MagicMock(
        side_effect=[{"_items": items}, {"_items": []}]
    )

    _, latest_created = advisory_connector.fetch_events()

    assert latest_created == "Mon, 20 Apr 2026 10:00:00 GMT"


def test_no_cursor_no_start_date_uses_30_days_ago(advisory_connector):
    advisory_connector.configuration.start_date = None
    advisory_connector.client.get_advisories = MagicMock(return_value={"_items": []})

    fixed_now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    with patch("xmco_modules.triggers.yuno_advisory.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        advisory_connector.fetch_events()

    call_kwargs = advisory_connector.client.get_advisories.call_args[1]
    where = call_kwargs["where"]
    assert "_created" in where
    cursor_used = where["_created"]["$gt"]
    assert "GMT" in cursor_used
    assert "+0000" not in cursor_used
    from email.utils import parsedate_to_datetime
    parsed = parsedate_to_datetime(cursor_used)
    expected = fixed_now - timedelta(days=30)
    assert abs((parsed - expected).total_seconds()) < 5


def test_no_cursor_with_start_date_uses_start_date(advisory_connector):
    advisory_connector.configuration.start_date = "Mon, 01 Jan 2024 00:00:00 GMT"
    advisory_connector.client.get_advisories = MagicMock(return_value={"_items": []})

    advisory_connector.fetch_events()

    call_kwargs = advisory_connector.client.get_advisories.call_args[1]
    where = call_kwargs["where"]
    assert where["_created"]["$gt"] == "Mon, 01 Jan 2024 00:00:00 GMT"


def test_existing_cursor_ignores_start_date(advisory_connector):
    advisory_connector.configuration.start_date = "Mon, 01 Jan 2024 00:00:00 GMT"
    advisory_connector._set_cursor("Thu, 8 Feb 2023 00:00:00 GMT")
    advisory_connector.client.get_advisories = MagicMock(return_value={"_items": []})

    advisory_connector.fetch_events()

    call_kwargs = advisory_connector.client.get_advisories.call_args[1]
    where = call_kwargs["where"]
    assert where["_created"]["$gt"] == "Thu, 8 Feb 2023 00:00:00 GMT"


def test_fetch_events_empty(advisory_connector):
    advisory_connector.client.get_advisories = MagicMock(return_value={"_items": []})
    events, latest_created = advisory_connector.fetch_events()
    assert events == []
    assert latest_created is None


def test_run_sleeps_between_cycles(advisory_connector):
    with patch.object(advisory_connector, "fetch_events", return_value=([], None)):
        with patch.object(advisory_connector, "_stop_event") as mock_stop:
            mock_stop.is_set.side_effect = [False, True]
            with patch("xmco_modules.triggers.yuno_advisory.time.sleep") as mock_sleep:
                advisory_connector.run()

    mock_sleep.assert_called_once_with(advisory_connector.configuration.frequency)


def test_push_events_batched(advisory_connector):
    items = [{"_id": str(i), "_created": f"Thu, {i+1} Feb 2023 00:00:00 GMT"} for i in range(120)]
    events_str = [json.dumps(item) for item in items]
    latest = items[-1]["_created"]

    with patch.object(advisory_connector, "fetch_events", return_value=(events_str, latest)):
        with patch.object(advisory_connector, "_stop_event") as mock_stop:
            mock_stop.is_set.side_effect = [False, True]
            with patch("xmco_modules.triggers.yuno_advisory.time.sleep"):
                advisory_connector.run()

    assert advisory_connector.push_events_to_intakes.call_count == 3
