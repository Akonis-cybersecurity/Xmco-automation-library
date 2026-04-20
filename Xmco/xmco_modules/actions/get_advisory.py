from sekoia_automation.action import Action

from xmco_modules import XmcoModule
from xmco_modules.client import XMCOClient


class GetAdvisoryAction(Action):
    module: XmcoModule

    @property
    def client(self) -> XMCOClient:
        return XMCOClient(
            api_key=self.module.configuration.api_key,
            base_url=self.module.configuration.base_url,
        )

    def run(self, arguments: dict) -> dict:
        advisory_id = arguments["advisory_id"]
        return self.client.get_advisory_by_id(advisory_id)
