from shutil import rmtree
from tempfile import mkdtemp
from unittest.mock import MagicMock

import pytest
from sekoia_automation import constants

from xmco_modules import XmcoModule
from xmco_modules.triggers.yuno_advisory import YunoAdvisoryConnector
from xmco_modules.triggers.yuno_ticket import YunoTicketConnector


@pytest.fixture
def data_storage():
    original_storage = constants.DATA_STORAGE
    constants.DATA_STORAGE = mkdtemp()

    yield constants.DATA_STORAGE

    rmtree(constants.DATA_STORAGE)
    constants.DATA_STORAGE = original_storage


@pytest.fixture
def module_configuration():
    return {
        "api_key": "test_api_key_secret",
        "base_url": "https://leportail.xmco.fr/api",
    }


@pytest.fixture
def advisory_connector(data_storage, module_configuration):
    module = XmcoModule()
    connector = YunoAdvisoryConnector(module=module, data_path=data_storage)
    connector.log = MagicMock()
    connector.log_exception = MagicMock()
    connector.push_events_to_intakes = MagicMock()
    connector.module.configuration = module_configuration
    connector.configuration = {
        "intake_key": "test_intake_key",
        "frequency": 60,
        "min_severity": None,
    }
    return connector


@pytest.fixture
def ticket_connector(data_storage, module_configuration):
    module = XmcoModule()
    connector = YunoTicketConnector(module=module, data_path=data_storage)
    connector.log = MagicMock()
    connector.log_exception = MagicMock()
    connector.push_events_to_intakes = MagicMock()
    connector.module.configuration = module_configuration
    connector.configuration = {
        "intake_key": "test_intake_key",
        "frequency": 60,
    }
    return connector


@pytest.fixture
def sample_advisory():
    return {
        "_id": "abc123",
        "ref": "XMCO-2023-001",
        "advisory_type": "PATCH",
        "severity": "high",
        "content_fr": {
            "title": "Patch critique OpenSSL",
            "description": "Une vulnérabilité critique a été découverte.",
            "remediation": "Mettre à jour vers la version 3.1.0",
        },
        "cve_refs": ["CVE-2023-0001"],
        "_created": "Thu, 8 Feb 2023 00:00:00 GMT",
        "_updated": "Thu, 8 Feb 2023 12:00:00 GMT",
    }


@pytest.fixture
def sample_ticket():
    return {
        "_id": "ticket456",
        "_etag": "etag_value_123",
        "title": "Review OpenSSL patch",
        "status": "new",
        "severity": "high",
        "_created": "Thu, 8 Feb 2023 00:00:00 GMT",
        "_updated": "Thu, 8 Feb 2023 12:00:00 GMT",
    }
