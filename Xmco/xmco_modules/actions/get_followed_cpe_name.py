from sekoia_automation.action import Action

from xmco_modules import XmcoModule
from xmco_modules.client import XMCOClient


class GetFollowedCpeNameAction(Action):
    module: XmcoModule

    @property
    def client(self) -> XMCOClient:
        return XMCOClient(
            api_key=self.module.configuration.api_key,
            base_url=self.module.configuration.base_url,
        )

    def run(self, arguments: dict) -> dict:
        return self.client.get_followed_cpe_names()
