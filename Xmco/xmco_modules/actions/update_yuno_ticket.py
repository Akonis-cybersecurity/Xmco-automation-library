from typing import Optional

from sekoia_automation.action import Action

from xmco_modules import XmcoModule
from xmco_modules.client import XMCOClient


class UpdateYunoTicketAction(Action):
    module: XmcoModule

    @property
    def client(self) -> XMCOClient:
        return XMCOClient(
            api_key=self.module.configuration.api_key,
            base_url=self.module.configuration.base_url,
        )

    def run(self, arguments: dict) -> dict:
        ticket_id: str = arguments["ticket_id"]
        etag: Optional[str] = arguments.get("etag")
        status: str = arguments["status"]
        severity: Optional[str] = arguments.get("severity")

        if not etag:
            ticket = self.client.get_yuno_ticket_by_id(ticket_id)
            etag = ticket.get("_etag", "")

        data: dict = {"status": status}
        if severity is not None:
            data["severity"] = severity

        return self.client.update_yuno_ticket(ticket_id=ticket_id, etag=etag, data=data)
