__version__ = "0.1.0"

from datetime import datetime
from zoneinfo import ZoneInfo

queensland_now = lambda: datetime.now(tz=ZoneInfo("Australia/Queensland"))
