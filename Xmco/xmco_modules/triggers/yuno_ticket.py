import json
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from functools import cached_property
from typing import List, Optional, Tuple

from sekoia_automation.connector import Connector
from sekoia_automation.storage import PersistentJSON

from xmco_modules import XmcoModule
from xmco_modules.client import XMCOClient
from xmco_modules.models import YunoTicketConnectorConfiguration

BATCH_SIZE = 50


class YunoTicketConnector(Connector):
    module: XmcoModule
    configuration: YunoTicketConnectorConfiguration

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ticket_context = PersistentJSON("ticket_context.json", self._data_path)

    @cached_property
    def client(self) -> XMCOClient:
        return XMCOClient(
            api_key=self.module.configuration.api_key,
            base_url=self.module.configuration.base_url,
        )

    def _get_cursor(self) -> Optional[str]:
        with self._ticket_context as cache:
            cursor = cache.get("last_ticket_cursor")
            if cursor:
                return cursor
        if self.configuration.start_date:
            if "GMT" not in self.configuration.start_date:
                self.log(
                    message=f"start_date '{self.configuration.start_date}' may not be in GMT format. "
                    "Expected format: 'Wed, 01 Jan 2026 00:00:00 GMT'",
                    level="warning",
                )
            return self.configuration.start_date
        default_start = datetime.now(timezone.utc) - timedelta(days=30)
        return default_start.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def _set_cursor(self, cursor: str) -> None:
        with self._ticket_context as cache:
            cache["last_ticket_cursor"] = cursor

    def _build_where(self, cursor: Optional[str]) -> Optional[dict]:
        if cursor:
            return {"_created": {"$gt": cursor}}
        return None

    def _parse_rfc2822(self, date_str: str):
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    def fetch_events(self) -> Tuple[List[str], Optional[str]]:
        cursor = self._get_cursor()
        where = self._build_where(cursor)
        events: List[str] = []
        latest_created: Optional[str] = None
        latest_dt = None
        page = 1

        while True:
            response = self.client.get_yuno_tickets(page=page, max_results=BATCH_SIZE, where=where)
            items = response.get("_items", [])
            if not items:
                break

            for item in items:
                events.append(json.dumps(item))
                item_created = item.get("_created")
                if item_created:
                    dt = self._parse_rfc2822(item_created)
                    if dt and (latest_dt is None or dt > latest_dt):
                        latest_dt = dt
                        latest_created = item_created

            if len(items) < BATCH_SIZE:
                break
            page += 1

        return events, latest_created

    def run(self) -> None:
        self.log(message="Starting XMCO Yuno Ticket connector", level="info")
        while self.running:
            try:
                events, latest_created = self.fetch_events()
                if events:
                    for i in range(0, len(events), BATCH_SIZE):
                        batch = events[i : i + BATCH_SIZE]
                        self.push_events_to_intakes(events=batch)
                    if latest_created:
                        self._set_cursor(latest_created)
                    self.log(message=f"Pushed {len(events)} ticket events to intake", level="info")
                else:
                    self.log(message="No new ticket events found", level="info")
            except Exception as e:
                self.log_exception(e, message="Error while fetching ticket events")
            time.sleep(self.configuration.frequency)
