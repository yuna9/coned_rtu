from __future__ import annotations
from abc import ABC, abstractmethod
from dateutil.parser import isoparse
import json

from configobj import ConfigObj
from pydantic import BaseModel, Field

from .reading import Reading

CONED_LOGIN_URL = "https://www.coned.com/en/login"
CONED_USAGE_URL = "https://www.coned.com/en/accounts-billing/dashboard?tab1=billingandusage-1&tab2=sectionEnergyBillingUsage-1&tab3=sectionRealTimeData-3"


def json_to_readings(usage_json):
    readings = []
    usage = json.loads(usage_json)
    for read in usage["reads"]:
        # Opower gives readings with null value for intervals that don't have data
        # yet, so skip them.
        if read["value"] is None:
            continue

        reading = Reading(
            isoparse(read["startTime"]),
            isoparse(read["endTime"]),
            usage["unit"],
            read["value"],
        )
        readings.append(reading)
    return readings


class Config(BaseModel):
    user: str = Field(alias="CONED_USER")
    password: str = Field(alias="CONED_PASS")
    totp: str = Field(alias="CONED_TOTP")
    account_id: str = Field(alias="OPOWER_ACCOUNT_ID")
    meter: int = Field(alias="OPOWER_METER")
    maid: str = Field(alias="CONED_MAID")

    @classmethod
    def from_config_obj(cls, obj: ConfigObj) -> Config:
        return cls(**obj)


class Coned(ABC):
    """
    Implementers of Coned are headless browsers that support JS and can query
    the underlying opower API to fetch real-time usage data.
    """

    @property
    def opower_usage_url(self):
        return f"https://cned.opower.com/ei/edge/apis/cws-real-time-ami-v1/cws/cned/accounts/{self.cfg.account_id}/meters/{self.cfg.meter}/usage"  # noqa

    @abstractmethod
    def __init__(self, config: Config):
        self.cfg = config

    @abstractmethod
    async def save_screenshot(self, filename: str):
        """
        Saves a 1080p screenshot of the page with the given filename in
        the screenshots folder. Doesn't reset the window size.
        """
        pass

    @abstractmethod
    async def login(self):
        pass

    @abstractmethod
    async def get_usage(self) -> list[Reading]:
        pass
