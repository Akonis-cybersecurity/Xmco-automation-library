from xmco_modules import XmcoModule
from xmco_modules.actions.get_advisory import GetAdvisoryAction
from xmco_modules.actions.get_cve import GetCVEAction
from xmco_modules.actions.get_followed_cpe_name import GetFollowedCpeNameAction
from xmco_modules.actions.get_vulnerability import GetVulnerabilityAction
from xmco_modules.actions.update_yuno_ticket import UpdateYunoTicketAction
from xmco_modules.triggers.yuno_advisory import YunoAdvisoryConnector
from xmco_modules.triggers.yuno_ticket import YunoTicketConnector

if __name__ == "__main__":
    module = XmcoModule()

    module.register(YunoAdvisoryConnector, "xmco_yuno_advisory")
    module.register(YunoTicketConnector, "xmco_yuno_ticket")
    module.register(GetAdvisoryAction, "get_advisory")
    module.register(GetVulnerabilityAction, "get_vulnerability")
    module.register(GetCVEAction, "get_cve")
    module.register(GetFollowedCpeNameAction, "get_followed_cpe_name")
    module.register(UpdateYunoTicketAction, "update_yuno_ticket")

    module.run()
