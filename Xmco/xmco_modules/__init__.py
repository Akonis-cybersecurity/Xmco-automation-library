from sekoia_automation.module import Module
from xmco_modules.models import XmcoModuleConfiguration


class XmcoModule(Module):
    configuration: XmcoModuleConfiguration
