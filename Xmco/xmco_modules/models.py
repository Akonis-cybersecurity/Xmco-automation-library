from typing import Optional

from pydantic.v1 import BaseModel, Field
from sekoia_automation.connector import DefaultConnectorConfiguration


class XmcoModuleConfiguration(BaseModel):
    api_key: str = Field(..., secret=True, description="XMCO API key")
    base_url: str = Field(
        default="https://leportail.xmco.fr/api",
        description="XMCO API base URL",
    )


class YunoAdvisoryConnectorConfiguration(DefaultConnectorConfiguration):
    frequency: int = Field(default=3600, description="Pull interval in seconds")
    min_severity: Optional[str] = Field(
        default=None,
        description="Minimum severity filter: urgent, high, medium, low",
    )
    start_date: Optional[str] = Field(
        default=None,
        description=(
            "Initial start date (RFC2822 format) for first run. "
            "Example: 'Mon, 01 Jan 2024 00:00:00 GMT'. "
            "If not set, defaults to 30 days ago."
        ),
    )


class YunoTicketConnectorConfiguration(DefaultConnectorConfiguration):
    frequency: int = Field(default=3600, description="Pull interval in seconds")
    start_date: Optional[str] = Field(
        default=None,
        description=(
            "Initial start date (RFC2822 format) for first run. "
            "Example: 'Mon, 01 Jan 2024 00:00:00 GMT'. "
            "If not set, defaults to 30 days ago."
        ),
    )
