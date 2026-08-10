"""Constants for the FurryTail integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "furrytail"
MANUFACTURER: Final = "FurryTail"
DEFAULT_NAME: Final = "FurryTail"

API_BASE: Final = "https://app.prod-iot.furrytail.net"
MERCHANT_ID: Final = "100000000000000000"
DEFAULT_LANG: Final = "en_US"
USER_AGENT: Final = "wuwei/1.0.16 (HomeAssistant; FurryTail)"

# Event IDs requested by the official app for litter history.
EVENT_IDS: Final = "25,26,28,27"
EVENT_VISIT: Final = 25

# Known datapoint IDs from MITM of FurryTail Home / PF001.
DP_CLEAN_STATE: Final = "24"
DP_VISIT_DURATION: Final = "20"
DP_VISIT_WEIGHT: Final = "21"
DP_LIGHT_BRIGHTNESS: Final = "22"
DP_AUTO_CLEAN: Final = "6"
DP_CLEAN_DELAY: Final = "8"

CONF_ACCOUNT: Final = "account"
CONF_TOKEN: Final = "token"

UPDATE_INTERVAL = timedelta(minutes=2)

PLATFORMS: Final = ["binary_sensor", "light", "sensor"]
