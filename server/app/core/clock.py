from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends

from app.core.config import Settings, get_settings


class Clock:
    """Single source of truth for 'now', driven by APP_NOW, in company time."""

    def __init__(self, now: datetime, tz_name: str):
        self._now = now
        self.tz = ZoneInfo(tz_name)

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.astimezone(self.tz).date()

    @staticmethod
    def week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    def current_week_start(self) -> date:
        return self.week_start(self.today())

    def last_closed_week_start(self) -> date:
        return self.current_week_start() - timedelta(days=7)

    def last_n_weeks(self, n: int = 13) -> list[date]:
        """Oldest first, ending with the current week."""
        cur = self.current_week_start()
        return [cur - timedelta(days=7 * i) for i in range(n - 1, -1, -1)]


def get_clock(settings: Settings = Depends(get_settings)) -> Clock:
    return Clock(settings.app_now, settings.company_timezone)
