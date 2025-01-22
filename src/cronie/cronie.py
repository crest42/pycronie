"""
Small decorator based implementation of Unix beloved crontab.

Usage:
import asyncio

@cron("* * * * *")
async def function():
    await asyncio.sleep(10)


"""

from typing import Callable, Any, Coroutine

import asyncio
import logging
from datetime import date, datetime, timedelta


__all__ = [
    "cron",
    "reboot",
    "startup",
    "shutdown",
    "minutely",
    "hourly",
    "midnight",
    "daily",
    "weekly",
    "monthly",
    "annually",
    "yearly",
    "run_cron",
    "CronJobInvalid",
]

AwaitableType = Callable[[], Coroutine[Any, Any, None]]
cron_list: list["CronJob"] = []
cron_startup_list: list["CronJob"] = []
cron_shutdown_list: list["CronJob"] = []
ANY = -1
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
DAYS_PER_MONTH = 31
MONTHS_PER_YEAR = 12
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
CRON_STRING_TEMPLATE_MINUTELY = "* * * * *"
CRON_STRING_TEMPLATE_HOURLY = "0 * * * *"
CRON_STRING_TEMPLATE_DAILY = "0 0 * * *"
CRON_STRING_TEMPLATE_WEEKLY = "0 0 * * 0"
CRON_STRING_TEMPLATE_MONTHLY = "0 0 1 * *"
CRON_STRING_TEMPLATE_ANNUALLY = "0 0 1 1 *"
ANY_MINUTE = range(0, MINUTES_PER_HOUR)
ANY_HOUR = range(0, HOURS_PER_DAY)
ANY_DAY = range(1, DAYS_PER_MONTH + 1)
ANY_MONTH = range(1, MONTHS_PER_YEAR)
ANY_WEEKDAY = range(0, 7)
log = logging.getLogger(__name__)
WEEKDAY_MAP = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


def cron(cron_format_string: str) -> Callable[[AwaitableType], AwaitableType]:
    """
    Decorator function to annotate cron jobs.

    Usage:
    @cron("* * * * *")
    async def job():
        pass
    """

    def decorator(func: AwaitableType) -> AwaitableType:
        try:
            cron_job = CronJob(func, cron_format_string)
            cron_list.append(cron_job)
        except CronJobInvalid:
            log.error(
                f"Could not setup cronjob for {func.__name__} on schedule '{cron_format_string}'"
            )
        return func

    return decorator


def reboot(func: AwaitableType) -> AwaitableType:
    """Runs once on startup"""
    try:
        cron_job = CronJob(func, "STARTUP")
        cron_startup_list.append(cron_job)
    except CronJobInvalid:
        log.error(f"Could not setup cronjob for {func.__name__} on '@startup' schedule")
    return func


def startup(func: AwaitableType) -> AwaitableType:
    """Runs once on startup"""
    return reboot(func)


def shutdown(func: AwaitableType) -> AwaitableType:
    """Runs once on shutdown"""
    try:
        cron_job = CronJob(func, "SHUTDOWN")
        cron_shutdown_list.append(cron_job)
    except CronJobInvalid:
        log.error(
            f"Could not setup cronjob for {func.__name__} on '@shutdown' schedule"
        )
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


def _cast_cron_int(maybe_int: str) -> int:
    try:
        return int(maybe_int)
    except ValueError as ex:
        raise InvalidCronStringException() from ex


def _is_leap_year(year: int) -> int:
    return (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)


def _get_next_leap_year(year: int) -> int:
    for i in range(year, year + 4):
        if _is_leap_year(i):
            return i
    raise ValueError(f"Could not find the next leap year for {year}")


def _is_leap_year_exclusive(month: int, day: int) -> bool:
    if month == 2 and day > 28:
        return True
    return False


def _get_next_best_fit(haystack: list[int], needle: int) -> int:
    if needle in haystack:
        return haystack.index(needle)

    for i, elem in enumerate(haystack):
        if needle > elem:
            continue
        return i
    return -1


def _detla_between_dates_in_minutes(first_date: date, second_date: date) -> int:
    return (first_date - second_date).days * MINUTES_PER_DAY


def _cast_cron_weekday(maybe_weekday: str) -> int:
    try:
        return int(maybe_weekday)
    except ValueError as e:
        try:
            return int(WEEKDAY_MAP[maybe_weekday])
        except KeyError:
            raise InvalidCronStringException(
                "Not a valid cron weekday number or string"
            ) from e


class InvalidCronStringException(Exception):
    """General Exception raised when cron string could not be parsed"""


class _CronStringParser:
    """Main Cron string parsing functionallity.

    Parses a cron string into sets of valid minutes, hours, days and weeks.
    Valid means that the cron can be executed at that timings.

    Used in CronJob to schedule job
    """

    def __init__(self, cron_format_string: str) -> None:
        self.format = cron_format_string
        if cron_format_string not in ["STARTUP", "SHUTDOWN"]:
            try:
                self._parse_format()
            except InvalidCronStringException as ex:
                log.error(
                    f"Invalid cron string '{cron_format_string}'. Exception while parsing"
                )
                raise ex
        self.valid = True

    def _validate_minute(self) -> None:
        if isinstance(self.valid_minutes, list):
            for elem in self.valid_minutes:
                if elem < 0 or elem > 59:
                    raise InvalidCronStringException(
                        f"Invalid cron minute {self.valid_minutes}"
                    )
                return
        raise InvalidCronStringException(f"Invalid cron minute {self.valid_minutes}")

    def _validate_hour(self) -> None:
        if isinstance(self.valid_hours, list):
            for elem in self.valid_hours:
                if elem < 0 or elem > 23:
                    raise InvalidCronStringException(
                        f"Invalid cron hour {self.valid_hours}"
                    )
                return
        raise InvalidCronStringException(f"Invalid cron hour {self.valid_hours}")

    def _validate_day(self) -> None:
        if isinstance(self.valid_days, list):
            for elem in self.valid_days:
                if elem < 1 or elem > 31:
                    raise InvalidCronStringException(
                        f"Invalid cron day {self.valid_days}"
                    )
                return
        raise InvalidCronStringException(f"Invalid cron day {self.valid_days}")

    def _validate_month(self) -> None:
        if isinstance(self.valid_months, list):
            for elem in self.valid_months:
                if elem < 1 or elem > 12:
                    raise InvalidCronStringException(
                        f"Invalid cron month {self.valid_months}"
                    )
                return
        raise InvalidCronStringException(f"Invalid cron month {self.valid_months}")

    def _validate_weekday(self) -> None:
        if isinstance(self.valid_weekdays, list):
            for elem in self.valid_weekdays:
                if elem < 0 or elem > 6:
                    raise InvalidCronStringException(
                        f"Invalid cron weekday {self.valid_weekdays}"
                    )
                return
        raise InvalidCronStringException(f"Invalid cron weekday {self.valid_weekdays}")

    def _validate(self) -> None:
        self._validate_minute()
        self._validate_hour()
        self._validate_day()
        self._validate_month()
        self._validate_weekday()

    def _try_parse_cron(
        self,
        cron_format_string: str,
        end: int,
        cast_function: Callable[[str], int] = _cast_cron_int,
    ) -> list[int]:
        assert isinstance(cron_format_string, str)
        values = []
        parts = cron_format_string.split(",")
        for part in parts:
            step_size = 1
            if "/" in part:
                step_size = int(part.split("/")[1])
                part = part[0 : part.index("/")]
            if "-" in part:
                start = cast_function(part.split("-")[0])
                end = cast_function(part.split("-")[1])
                values.extend(list(range(start, end + 1, step_size)))
            else:
                start = cast_function(part)
                values.extend(
                    list(range(start, end if step_size > 1 else start + 1, step_size))
                )
        return values

    def _try_parse_cron_minute(self, cron_minute: str) -> list[int]:
        if cron_minute.startswith("*"):
            if "/" in cron_minute:
                step_size = int(cron_minute.split("/")[1])
                return list(range(ANY_MINUTE.start, ANY_MINUTE.stop, step_size))
            return list(ANY_MINUTE)
        return self._try_parse_cron(cron_minute, ANY_MINUTE.stop)

    def _try_parse_cron_hour(self, cron_hour: str) -> list[int]:
        if cron_hour.startswith("*"):
            if "/" in cron_hour:
                step_size = int(cron_hour.split("/")[1])
                return list(range(ANY_HOUR.start, ANY_HOUR.stop, step_size))
            return list(ANY_HOUR)
        return self._try_parse_cron(cron_hour, ANY_HOUR.stop)

    def _try_parse_cron_day(self, cron_day: str) -> list[int]:
        if cron_day.startswith("*"):
            if "/" in cron_day:
                step_size = int(cron_day.split("/")[1])
                return list(range(ANY_DAY.start, ANY_DAY.stop, step_size))
            return list(ANY_DAY)
        return self._try_parse_cron(cron_day, ANY_DAY.stop)

    def _try_parse_cron_month(self, cron_month: str) -> list[int]:
        if cron_month.startswith("*"):
            if "/" in cron_month:
                step_size = int(cron_month.split("/")[1])
                return list(range(ANY_MONTH.start, ANY_MONTH.stop, step_size))
            return list(ANY_MONTH)
        return self._try_parse_cron(cron_month, ANY_MONTH.stop)

    def _try_parse_cron_weekday(self, cron_weekday: str) -> list[int]:
        cron_weekday = cron_weekday.replace("sun", str(0))
        cron_weekday = cron_weekday.replace("mon", str(1))
        cron_weekday = cron_weekday.replace("tue", str(2))
        cron_weekday = cron_weekday.replace("wed", str(3))
        cron_weekday = cron_weekday.replace("thu", str(4))
        cron_weekday = cron_weekday.replace("fri", str(5))
        cron_weekday = cron_weekday.replace("sat", str(6))
        if cron_weekday.startswith("*") and not "/" in cron_weekday:
            return list(ANY_WEEKDAY)
        weekdays = self._try_parse_cron(
            cron_weekday, ANY_WEEKDAY.stop, cast_function=_cast_cron_weekday
        )
        for i, elem in enumerate(weekdays):
            if elem == 7:
                weekdays[i] = 0
        return weekdays

    def _parse_format(self) -> None:
        parts = self.format.split(" ")
        if len(parts) != 5:
            raise RuntimeError(f"Cron string {self.format} is not a valid cron string")

        # TODO USE ranges?
        self.valid_minutes = self._try_parse_cron_minute(parts[0])
        self.valid_hours = self._try_parse_cron_hour(parts[1])
        self.valid_days = self._try_parse_cron_day(parts[2])
        self.valid_months = self._try_parse_cron_month(parts[3])
        self.valid_weekdays = self._try_parse_cron_weekday(parts[4])
        self._validate()


class CronJobInvalid(Exception):
    """General Exception raised when cron job could not be created e. g. due to a invalid string"""


class CronJob:
    """Main Wrapper for a single Cronjob. Includes the target function, cron string parsing, and timing information."""

    def __init__(self, awaitable: AwaitableType, cron_format_string: str) -> None:
        log.debug(f"Create new cron with {cron_format_string=} {awaitable=}")
        if not isinstance(cron_format_string, str):
            raise RuntimeError("Cron format string expected to be a string")
        self.format = cron_format_string
        self.awaitable = awaitable
        if cron_format_string not in ["STARTUP", "SHUTDOWN"]:
            try:
                self.parsed = _CronStringParser(self.format)
            except InvalidCronStringException as ex:
                raise CronJobInvalid() from ex
            self._schedule(CronJob._get_current_time())

    @property
    def months(self) -> list[int]:
        """Months on which this cron can run. Range 1-12"""
        return self.parsed.valid_months

    @property
    def weekdays(self) -> list[int]:
        """Weekdays on which this cron can run. Range 0(sun)-6(sat)"""
        return self.parsed.valid_weekdays

    @property
    def days(self) -> list[int]:
        """Days on which this cron can run. Range 1-31"""
        return self.parsed.valid_days

    @property
    def hours(self) -> list[int]:
        """Hours on which this cron can run. Range 0-23"""
        return self.parsed.valid_hours

    @property
    def minutes(self) -> list[int]:
        """Minutes on which this cron can run. Range 0-23"""
        return self.parsed.valid_minutes

    @classmethod
    def _get_current_time(cls) -> datetime:
        current_time = datetime.now()
        current_time = current_time - timedelta(seconds=current_time.second)
        current_time = current_time - timedelta(microseconds=current_time.microsecond)
        return current_time

    def _update_month(self, next_run: datetime) -> datetime:
        index = _get_next_best_fit(self.months, next_run.month)
        if self.months[index] == next_run.month:
            log.debug(f"Cron month {next_run.month} is in range. Continue")
            return next_run
        if (
            index == -1
        ):  # Wraps year. Need to wrap year and do leap year sanity check here
            if _is_leap_year_exclusive(self.months[0], self.days[0]):
                year = _get_next_leap_year(next_run.year + 1)
            else:
                year = next_run.year + 1
            delta = _detla_between_dates_in_minutes(
                date(year, self.months[0], self.days[0]), next_run.date()
            )
        else:  # Same year TODO: Test case for invalid day/month comb. e. g. 31st of April
            delta = _detla_between_dates_in_minutes(
                date(next_run.year, self.months[index], self.days[0]), next_run.date()
            )
        return (next_run + timedelta(minutes=delta)).replace(
            hour=self.hours[0], minute=self.minutes[0]
        )

    def _update_day(self, next_run: datetime) -> datetime:
        index = _get_next_best_fit(self.days, next_run.day)
        if self.days[index] == next_run.day:
            log.debug(f"Cron day {next_run.day} is in range. Continue")
            return next_run
        if index == -1:
            delta = _detla_between_dates_in_minutes(
                date(next_run.year, next_run.month + 1, self.days[0]), next_run.date()
            )
        else:
            if next_run.month == 2 and self.days[index] > 28:
                year = _get_next_leap_year(next_run.year)
            else:
                year = next_run.year
            delta = _detla_between_dates_in_minutes(
                date(year, next_run.month, self.days[index]), next_run.date()
            )
        return (next_run + timedelta(minutes=delta)).replace(
            hour=self.hours[0], minute=self.minutes[0]
        )

    def _update_hour(self, next_run: datetime) -> datetime:
        index = _get_next_best_fit(self.hours, next_run.hour)
        if self.hours[index] == next_run.hour:
            log.debug(f"Cron hour {next_run.hour} is in range. Continue")
            return next_run
        if index == -1:
            delta = ((HOURS_PER_DAY - next_run.hour) + self.hours[0]) * MINUTES_PER_HOUR
        else:
            delta = (self.hours[index] - next_run.hour) * MINUTES_PER_HOUR
        return (next_run + timedelta(minutes=delta)).replace(minute=self.minutes[0])

    def _update_minute(self, next_run: datetime) -> datetime:
        index = _get_next_best_fit(self.minutes, next_run.minute)
        if self.minutes[index] == next_run.minute:
            log.debug(f"Cron minute {next_run.minute} is in range. Continue")
            return next_run
        if index == -1:
            delta = MINUTES_PER_HOUR - next_run.minute + self.minutes[0]
        else:
            delta = self.minutes[index] - next_run.minute
        return next_run + timedelta(minutes=delta)

    def _update_weekday(self, next_run: datetime) -> datetime:
        weekday = next_run.isoweekday() if next_run.isoweekday() < 7 else 0
        index = _get_next_best_fit(self.weekdays, weekday)
        if self.weekdays[index] == weekday:
            log.debug(f"Cron weekday {weekday} is in range. Continue")
            return next_run

        if index == -1:
            first_weekday = self.weekdays[0]
            delta = ((7 - weekday) + first_weekday) * MINUTES_PER_DAY
        else:
            delta = (self.weekdays[index] - weekday) * MINUTES_PER_DAY
        return (next_run + timedelta(minutes=delta)).replace(
            hour=self.hours[0], minute=self.minutes[0]
        )

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

        if len(self.days) == 31 and len(self.weekdays) < 7:
            log.debug(
                "Day is ANY and weekday is specific range -> choose weekday over day"
            )
            next_run = weekday
        elif len(self.days) < 31 and len(self.weekdays) < 7:
            log.debug("Both day and weekday are not ANY -> choose next execution day")
            next_run = min(day, weekday)
        else:
            log.debug("Weekday is ANY -> choose day")
            next_run = day

        log.debug(f"update month on {next_run}")
        next_run = self._update_month(next_run)

        return next_run

    def _schedule(self, current_time: datetime) -> None:
        """Updates Job scheduling. Sets next run date in reference to the input date (e. g. now).

        Needs to be run after each job execution. to ensure next scheduling

        Args:
            current_time (datetime): Reference time for which the scheduling should be calculated
        """
        next_run = current_time + timedelta(minutes=1)
        log.debug(
            f"Start validating next execution day for {self}. Earliest execution time is {next_run}"
        )
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
        self._schedule(now)

    def due_in(self, now: datetime) -> int:
        """Returns seconds until the cron needs to be scheduled based on relative time input"""
        due_in = (self.next - now).total_seconds()
        return (
            int(due_in) + 1
        )  # Second precision is fine since cron operates on minutes


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

    FMT = "* * * * *"
    expected = datetime(year=2024, month=6, day=15, hour=12, minute=14, second=0)
    cron_ = CronJob(_id, FMT).next
    assert cron_ == expected

    log.info(f"{FMT} = {cron_=} == {expected=}")
