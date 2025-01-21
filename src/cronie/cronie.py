"""
Small decorator based implementation of Unix beloved crontab.

Usage:
import asyncio

@cron("* * * * *")
async def function():
    await asyncio.sleep(10)


"""

from typing import Callable, Awaitable, Any, Coroutine, Never

import asyncio
import logging
from datetime import date, datetime, timedelta

AwaitableType = Callable[[], Coroutine[Any, Any, None]]
cron_list: list["CronJob"] = []
cron_startup_list: list["CronJob"] = []
cron_shutdown_list: list["CronJob"] = []
ANY = -1
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
DAYS_PER_MONTH = 31
MONTHS_PER_YEAR = 12
CRON_MONTH_BOUNDS = (1, MONTHS_PER_YEAR)
CRON_DAY_BOUNDS = (1, DAYS_PER_MONTH)
CRON_HOUR_BOUNDS = (0, HOURS_PER_DAY - 1)
CRON_MINUTE_BOUNDS = (0, MINUTES_PER_HOUR - 1)
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
CRON_STRING_TEMPLATE_MINUTELY = "* * * * *"
CRON_STRING_TEMPLATE_HOURLY = "0 * * * *"
CRON_STRING_TEMPLATE_DAILY = "0 0 * * *"
CRON_STRING_TEMPLATE_WEEKLY = "0 0 * * 0"
CRON_STRING_TEMPLATE_MONTHLY = "0 0 1 * *"
CRON_STRING_TEMPLATE_ANNUALLY = "0 0 1 1 *"

log = logging.getLogger(__name__)


def cron(cron_format_string: str) -> Callable[[AwaitableType], AwaitableType]:
    """
    Decorator function to annotate cron jobs.

    Usage:
    @cron("* * * * *")
    async def job():
        pass
    """

    def decorator(f: AwaitableType)-> AwaitableType:
        cron_list.append(CronJob(f, cron_format_string))
        return f

    return decorator


def reboot(func: AwaitableType) -> AwaitableType:
    """Runs once on startup"""
    cron_startup_list.append(CronJob(func, "STARTUP"))
    return func


def startup(func: AwaitableType)->AwaitableType:
    """Runs once on startup"""
    return reboot(func)


def shutdown(func:AwaitableType)-> AwaitableType:
    """Runs once on shutdown"""
    cron_shutdown_list.append(CronJob(func, "SHUTDOWN"))
    return func


def minutely(func: AwaitableType) -> AwaitableType:
    """Runs every minute"""
    return cron(CRON_STRING_TEMPLATE_MINUTELY)(func)


def hourly(func: AwaitableType) -> AwaitableType:
    """Runs once every hour"""
    return cron(CRON_STRING_TEMPLATE_HOURLY)(func)


def midnight(func: AwaitableType) -> AwaitableType:
    """Runs once a day at midnight"""
    return cron(CRON_STRING_TEMPLATE_DAILY)(func)


def daily(func: AwaitableType) -> AwaitableType:
    """Runs once a day at midnight"""
    return cron(CRON_STRING_TEMPLATE_DAILY)(func)


def weekly(func: AwaitableType) -> AwaitableType:
    """Runs once a week at Sunday midnight"""
    return cron(CRON_STRING_TEMPLATE_WEEKLY)(func)


def monthly(func: AwaitableType) -> AwaitableType:
    """Runs once a month at the 1st on midnight"""
    return cron(CRON_STRING_TEMPLATE_MONTHLY)(func)


def annually(func: AwaitableType) -> AwaitableType:
    """Runs once a year on the 1st of Janurary midnight"""
    return cron(CRON_STRING_TEMPLATE_ANNUALLY)(func)


def yearly(func: AwaitableType) -> AwaitableType:
    """Runs once a year on the 1st of Janurary midnight"""
    return cron(CRON_STRING_TEMPLATE_ANNUALLY)(func)


class CronJob:
    """Main Wrapper for a single Cronjob. Includes the target function, cron string parsing, and timing information."""

    weekday_map = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}

    def __init__(self, awaitable: AwaitableType, cron_format_string: str) -> None:
        if not isinstance(cron_format_string, str):
            raise RuntimeError("Cron format string expected to be a string")
        self.format = cron_format_string
        self.awaitable = awaitable
        if cron_format_string not in ["STARTUP", "SHUTDOWN"]:
            self._parse_format()
            self._update(CronJob._get_current_time())

    @classmethod
    def _get_current_time(cls) -> datetime:
        current_time = datetime.now()
        current_time = current_time - timedelta(seconds=current_time.second)
        current_time = current_time - timedelta(microseconds=current_time.microsecond)
        return current_time

    def _adjust_minutes(self, next_run: datetime) -> int:
        adjusted = 0
        first_minute = self.minute[0]
        if first_minute < next_run.minute:
            adjusted += next_run.minute - first_minute
        return adjusted

    def _adjust_hours(self, next_run: datetime) -> int:
        adjusted = self._adjust_minutes(next_run)
        first_hour = self.hour[0]
        if first_hour < next_run.hour:
            adjusted += MINUTES_PER_HOUR * (next_run.hour - first_hour)
        return adjusted

    def _adjust_days(self, next_run: datetime) -> int:
        adjusted = self._adjust_hours(next_run)
        first_day = self.day[0]
        if first_day < next_run.day:
            adjusted += (
                MINUTES_PER_DAY
                * (
                    date(next_run.year, next_run.month, next_run.day)
                    - date(next_run.year, next_run.month, first_day)
                ).days
            )
        return adjusted

    def _update_month(self, next_run: datetime) -> datetime:
        if next_run.month in self.month:
            return next_run
        for elem in self.month:
            if elem >= next_run.month:
                minutes = (
                    date(next_run.year, elem, next_run.day)
                    - date(next_run.year, next_run.month, next_run.day)
                ).days * MINUTES_PER_DAY
                minutes -= self._adjust_days(next_run)
                return next_run + timedelta(minutes=minutes)
        next_month = self.month[0]
        minutes = 0
        for i in range(4):
            try:
                minutes = (
                    date(next_run.year + i+1, next_month, next_run.day)
                    - date(next_run.year, next_run.month, next_run.day)
                ).days * MINUTES_PER_DAY
                break
            except ValueError:
                pass
        minutes -= self._adjust_days(next_run)
        return next_run + timedelta(minutes=minutes)

    def _update_weekday(self, next_run: datetime) -> datetime:
        weekday = next_run.isoweekday() if next_run.isoweekday() < 7 else 0
        if weekday in self.weekday:
            return next_run

        for elem in self.weekday:
            if elem > weekday:
                day = next_run.day + (elem-weekday)
                minutes = (
                    date(next_run.year, next_run.month, day)
                    - date(next_run.year, next_run.month, next_run.day)
                ).days * MINUTES_PER_DAY
                minutes -= self._adjust_hours(next_run)
                return next_run + timedelta(minutes=minutes)
        first_weekday = self.weekday[0]
        day = next_run.day + ((7-weekday)+first_weekday)
        minutes = (
            date(next_run.year, next_run.month, day)
            - date(next_run.year, next_run.month, next_run.day)
        ).days * MINUTES_PER_DAY
        minutes -= self._adjust_hours(next_run)
        return next_run + timedelta(minutes=minutes)

    def _update_day(self, next_run: datetime) -> datetime:
        if next_run.day in self.day:
            return next_run
        for elem in self.day:
            if elem > next_run.day:
                minutes = (
                    date(next_run.year, next_run.month, elem)
                    - date(next_run.year, next_run.month, next_run.day)
                ).days * MINUTES_PER_DAY
                minutes -= self._adjust_hours(next_run)
                return next_run + timedelta(minutes=minutes)
        next_day = self.day[0]
        minutes = (
            date(next_run.year, next_run.month + 1, next_day)
            - date(next_run.year, next_run.month, next_run.day)
        ).days * MINUTES_PER_DAY

        minutes -= self._adjust_hours(next_run)
        return next_run + timedelta(minutes=minutes)

    def _update_hour(self, next_run: datetime) -> datetime:
        if next_run.hour in self.hour:
            return next_run
        for elem in self.hour:
            if elem > next_run.hour:
                minutes = (elem - next_run.hour) * MINUTES_PER_HOUR
                minutes -= self._adjust_minutes(next_run)
                return next_run + timedelta(minutes=minutes)
        next_hour = self.hour[0]
        minutes = (HOURS_PER_DAY - (next_run.hour - next_hour)) * MINUTES_PER_HOUR
        minutes -= self._adjust_minutes(next_run)
        return next_run + timedelta(minutes=minutes)

    def _update_minute(self, next_run: datetime) -> datetime:
        for elem in self.minute:
            if elem > next_run.minute:
                difference = elem - next_run.minute
                return next_run + timedelta(minutes=difference)
            if elem == next_run.minute:
                pass
                # return next_run + timedelta(minutes=1)

        next_minute = self.minute[0]
        diff = MINUTES_PER_HOUR - (next_run.minute - next_minute)
        return next_run + timedelta(minutes=diff)

    def _update_time(self, next_run: datetime) -> datetime:
        log.debug(f"update minute on {next_run}")
        next_run = self._update_minute(next_run)
        log.debug(f"update hour on {next_run}")
        next_run = self._update_hour(next_run)
        return next_run

    def _update_date(self, next_run: datetime) -> datetime:

        log.debug(f"update weekday on {next_run}")
        weekday = self._update_weekday(next_run)
        log.debug(f"update day on {next_run}")
        day = self._update_day(next_run)
        log.debug(f"Use min({weekday},{day})")

        if len(self.day) == 31 and len(self.weekday) < 7:
            next_run = weekday
        elif len(self.day) < 31 and len(self.weekday) < 7:
            next_run = min(day, weekday)
        else:
            next_run = day

        log.debug(f"update month on {next_run}")
        next_run = self._update_month(next_run)


        return next_run

    def _update(self, current_time: datetime) -> None:
        """Updates Job scheduling. Sets next run date in reference to the input date (e. g. now).

        Needs to be run after each job execution. to ensure next scheduling

        Args:
            current_time (datetime): Reference time for which the scheduling should be calculated
        """
        next_run = current_time
        next_run = self._update_time(next_run)
        next_run = self._update_date(next_run)

        if next_run == current_time:
            next_run = next_run + timedelta(minutes=0)

        assert next_run >= current_time
        self.next = next_run
        log.debug(f"next run at {next_run} ({self.due_in(current_time)}s)")

    async def run(self, now: datetime) -> None:
        """Executes a cron job.

        This function runs the cronjob and calculates the next point in time
        it needs to be schduled in reference to the input time

        Args:
            now (datetime): Time reference to calculate next scheduling.
        """
        await self.awaitable()
        self._update(now)

    def due_in(self, now: datetime) -> int:
        """Returns seconds until the cron needs to be scheduled based on relative time input"""
        due_in = (self.next - now).total_seconds()
        return (
            int(due_in) + 1 #TODO Hacky?
        )  # Second precision is fine since cron operates on minutes

    def _validate_minute(self) -> None:
        if isinstance(self.minute, list):
            for elem in self.minute:
                if elem < 0 or elem > 59:
                    raise TypeError(f"Invalid cron minute {self.minute}")
                return
        raise TypeError(f"Invalid cron minute {self.minute}")

    def _validate_hour(self) -> None:
        if isinstance(self.hour, list):
            for elem in self.hour:
                if elem < 0 or elem > 23:
                    raise TypeError(f"Invalid cron hour {self.hour}")
                return
        raise TypeError(f"Invalid cron minute {self.hour}")

    def _validate_day(self) -> None:
        if isinstance(self.day, list):
            for elem in self.day:
                if elem < 1 or elem > 31:
                    raise TypeError(f"Invalid cron hour {self.day}")
                return
        raise TypeError(f"Invalid cron minute {self.day}")

    def _validate_month(self) -> None:
        if isinstance(self.month, list):
            for elem in self.month:
                if elem < 1 or elem > 12:
                    raise TypeError(f"Invalid cron hour {self.month}")
                return
        raise TypeError(f"Invalid cron minute {self.month}")

    def _validate_weekday(self) -> None:
        if isinstance(self.weekday, list):
            for elem in self.weekday:
                if elem < 0 or elem > 6:
                    raise TypeError(f"Invalid cron weekday {self.weekday}")
                return
        raise TypeError(f"Invalid cron minute {self.weekday}")

    def _validate(self) -> None:
        self._validate_minute()
        self._validate_hour()
        self._validate_day()
        self._validate_month()
        self._validate_weekday()

    def _try_parse_cron(
        self, cron_format_string: str, lower: int, upper: int
    ) -> list[int]:
        assert isinstance(cron_format_string, str)
        if cron_format_string.startswith("*"):
            step_size = 1
            if "/" in cron_format_string:
                step_size = int(cron_format_string.split("/")[1])
            return list(range(lower, upper + 1, step_size))

        values = []
        parts = cron_format_string.split(",")
        for part in parts:
            step_size = 1
            if "/" in part:
                step_size = int(part.split("/")[1])
                part = part[0 : part.index("/")]
            if "-" in part:
                start = int(part.split("-")[0])
                end = int(part.split("-")[1])
                values.extend(list(range(start, end + 1, step_size)))
            else:
                values.append(int(part))
        return values

    def _try_parse_cron_minute(self, cron_minute: str) -> list[int]:
        return self._try_parse_cron(
            cron_minute, CRON_MINUTE_BOUNDS[0], CRON_MINUTE_BOUNDS[1]
        )

    def _try_parse_cron_hour(self, cron_hour: str) -> list[int]:
        return self._try_parse_cron(cron_hour, CRON_HOUR_BOUNDS[0], CRON_HOUR_BOUNDS[1])

    def _try_parse_cron_day(self, cron_day: str) -> list[int]:
        return self._try_parse_cron(cron_day, CRON_DAY_BOUNDS[0], CRON_DAY_BOUNDS[1])

    def _try_parse_cron_month(self, cron_month: str) -> list[int]:
        return self._try_parse_cron(
            cron_month, CRON_MONTH_BOUNDS[0], CRON_MONTH_BOUNDS[1]
        )

    def _try_parse_cron_weekday(self, cron_weekday: str) -> list[int]:
        cron_weekday = cron_weekday.replace("sun", str(0))
        cron_weekday = cron_weekday.replace("mon", str(1))
        cron_weekday = cron_weekday.replace("tue", str(2))
        cron_weekday = cron_weekday.replace("wed", str(3))
        cron_weekday = cron_weekday.replace("thu", str(4))
        cron_weekday = cron_weekday.replace("fri", str(5))
        cron_weekday = cron_weekday.replace("sat", str(6))
        weekdays = self._try_parse_cron(cron_weekday, 0, 6)
        for i, elem in enumerate(weekdays):
            if elem == 7:
                weekdays[i] = 0
        return weekdays

    def _parse_format(self) -> None:
        parts = self.format.split(" ")
        if len(parts) != 5:
            raise RuntimeError(f"Cron string {self.format} is not a valid cron string")
        else:
            self.minute = self._try_parse_cron_minute(parts[0])
            self.hour = self._try_parse_cron_hour(parts[1])
            self.day = self._try_parse_cron_day(parts[2])
            self.month = self._try_parse_cron_month(parts[3])
            self.weekday = self._try_parse_cron_weekday(parts[4])
        self._validate()


def _get_next(now: datetime) -> CronJob:
    """Returns next cron job that is due for execution"""
    next_cron = cron_list[0]
    for cron_job in cron_list[1:]:
        if cron_job.due_in(now) < next_cron.due_in(now):
            next_cron = cron_job
    return next_cron


async def _start_cron() -> None:
    for cron_job in cron_startup_list:
        await cron_job.awaitable()
    while True:
        now = datetime.now()
        next_cron = _get_next(now)
        for cron_job in cron_list:
            if next_cron.due_in(now) >= cron_job.due_in(now):
                log.info(
                    f"cron available in {cron_job.due_in(now)}: {cron_job.awaitable.__name__}"
                )
        await asyncio.sleep(max(1, next_cron.due_in(now)))
        for cron_job in cron_list:
            now = datetime.now()
            if now >= cron_job.next:
                log.info(f"{cron_job.format}: {cron_job.due_in(now)} {cron_job.next}")
                await cron_job.run(now)


def run_cron() -> None:
    """Runs the scheduler. Ensures the execution of discovered cronjobs and updates timinings"""
    try:
        asyncio.run(_start_cron())
    except KeyboardInterrupt:
        with asyncio.Runner() as runner:
            for cron_job in cron_shutdown_list:
                runner.run((cron_job.awaitable()))

if __name__ == "__main__":
    mock_dt = datetime(year=2024, month=6, day=15, hour=12, minute=13, second=0)
    logging.basicConfig()
    logging.root.setLevel(logging.DEBUG)

    async def _id() -> None:
        pass

    def _get_mock_time() -> datetime:
        return mock_dt

    setattr(CronJob, "_get_current_time", _get_mock_time)

    test_strings = {
        "* * * * *": datetime(year=2024, month=6, day=15, hour=12, minute=14, second=0),
        "0 * * * *": datetime(
            year=2024, month=6, day=15, hour=13, minute=0, second=0
        ),  # Before Current minute
        "59 * * * *": datetime(
            year=2024,
            month=6,
            day=15,
            hour=12,
            minute=59,
            second=0,  # After Current Minute
        ),
        "20 0 * * *": datetime(
            year=2024, month=6, day=16, hour=0, minute=20, second=0
        ),  # Before Current Hour
        "* 0 * * *": datetime(
            year=2024, month=6, day=16, hour=0, minute=0, second=0
        ),  # Before Current Hour
        "* 23 * * *": datetime(
            year=2024, month=6, day=15, hour=23, minute=0, second=0
        ),  # After Current Hour
        "* * 1 * *": datetime(
            year=2024, month=7, day=1, hour=0, minute=0, second=0
        ),  # Before Current Day
        "* * 30 * *": datetime(
            year=2024, month=6, day=30, hour=0, minute=0, second=0
        ),  # After Current Day
        "* * * 1 *": datetime(
            year=2025, month=1, day=1, hour=0, minute=0, second=0
        ),  # Before Current Month
        "* * * 12 *": datetime(
            year=2024, month=12, day=1, hour=0, minute=0, second=0
        ),  #  After Current Day

        "* * * * 6": datetime(
            year=2024, month=6, day=15, hour=12, minute=14, second=0
        ),  #  Every Monday
        "* * * * 1": datetime(
            year=2024, month=6, day=17, hour=0, minute=0, second=0
        ),  #  Every Monday

        "* * 16 * 1": datetime(
            year=2024, month=6, day=16, hour=0, minute=0, second=0
        ),  #  Every Monday or the 16th

        "* * 18 * 1": datetime(
            year=2024, month=6, day=17, hour=0, minute=0, second=0
        ),  #  Every Monday or the 1th


        "42 23 24 12 *": datetime(
            year=2024, month=12, day=24, hour=23, minute=42, second=0
        ),
        "1 1 1 1 *": datetime(year=2025, month=1, day=1, hour=1, minute=1, second=0),
        "0 0 1 1 *": datetime(year=2025, month=1, day=1, hour=0, minute=0, second=0),
        "15 14 1 * *": datetime(
            year=2024, month=7, day=1, hour=14, minute=15, second=0
        ),  # At 14:15 on day-of-month 1.
        "0 22 * * *": datetime(
            year=2024, month=6, day=15, hour=22, minute=0, second=0
        ),  # At 22:00 on every day-of-week
        "0 4 8-14 * *": datetime(
            year=2024, month=7, day=8, hour=4, minute=0, second=0
        ),  # At 04:00 on every day-of-month from 8 through 14.
    }

    gpt_cron_test_cases = {
        "* * * * *": datetime(2024, 6, 15, 12, 14, 0),
        "*/2 * * * *": datetime(2024, 6, 15, 12, 14, 0),
        "0 * * * *": datetime(2024, 6, 15, 13, 0, 0),
        "0 0 * * *": datetime(2024, 6, 16, 0, 0, 0),
        "30 14 * * *": datetime(2024, 6, 15, 14, 30, 0),
        "15,45 12 * * *": datetime(2024, 6, 15, 12, 15, 0),
        "0 0 1 * *": datetime(2024, 7, 1, 0, 0, 0),
        "0 12 15 * *": datetime(2024, 7, 15, 12, 0, 0),
        "30 8 15 6 *": datetime(2025, 6, 15, 8, 30, 0),
        "0 0 * * 0": datetime(2024, 6, 16, 0, 0, 0),
        "0 0 * * 1": datetime(2024, 6, 17, 0, 0, 0),
        "0 0 29 2 *": datetime(2028, 2, 29, 0, 0, 0),
        "*/15 * * * *": datetime(2024, 6, 15, 12, 15, 0),
        "5-10 * * * *": datetime(2024, 6, 15, 13, 5, 0),
        "0 9-17 * * 1-5": datetime(2024, 6, 17, 9, 0, 0),
        "0 0 1 1 *": datetime(2025, 1, 1, 0, 0, 0),
        "*/5 12 * * 3": datetime(2024, 6, 19, 12, 0, 0),
        "0 0 15 6 6": datetime(2024, 6, 22, 0, 0, 0),
        "0 10 1-7 * 1": datetime(2024, 6, 17, 10, 0, 0),
        "*/10 14 * * 2": datetime(2024, 6, 18, 14, 0, 0),
    }
    for fmt, expected in test_strings.items():
        cron_ = CronJob(cron(fmt)(_id), fmt).next
        log.info(f"{fmt} = {cron_=} == {expected=}")
        assert cron_ == expected

    for fmt, expected in gpt_cron_test_cases.items():
        cron_ = CronJob(cron(fmt)(_id), fmt).next
        log.info(f"{fmt} = {cron_=} == {expected=}")
        assert cron_ == expected
