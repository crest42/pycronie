"""Small decorator based implementation of Unix beloved crontab."""

from typing import Callable, Any, Coroutine, List, Optional

import asyncio
import logging
import inspect
from datetime import date, datetime, timedelta
import functools

AwaitableType = Callable[[], Coroutine[Any, Any, None]]
DEFAULT_EVENTLOOP_DELAY = 60
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


class CronJobInvalid(Exception):
    """General Exception raised when cron job could not be created e. g. due to a invalid string."""


class InvalidCronStringException(Exception):
    """General Exception raised when cron string could not be parsed."""


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


class _CronStringParser:
    """Main Cron string parsing functionallity.

    Parses a cron string into sets of valid minutes, hours, days and weeks.
    Valid means that the cron can be executed at that timings.

    Used in _CronJob to schedule job
    """

    def __init__(self, schedule: str) -> None:
        self.format = schedule
        if schedule not in ["STARTUP", "SHUTDOWN"]:
            try:
                self._parse_format()
            except InvalidCronStringException as ex:
                log.error(f"Invalid cron string '{schedule}'. Exception while parsing")
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
        schedule: str,
        end: int,
        cast_function: Callable[[str], int] = _cast_cron_int,
    ) -> list[int]:
        assert isinstance(schedule, str)
        values = []
        parts = schedule.split(",")
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
        if cron_weekday.startswith("*") and "/" not in cron_weekday:
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

        self.valid_minutes = self._try_parse_cron_minute(parts[0])
        self.valid_hours = self._try_parse_cron_hour(parts[1])
        self.valid_days = self._try_parse_cron_day(parts[2])
        self.valid_months = self._try_parse_cron_month(parts[3])
        self.valid_weekdays = self._try_parse_cron_weekday(parts[4])
        self._validate()


class _CronJob:
    """Main Wrapper for a single Cronjob. Includes the target function, cron string parsing, and timing information."""

    def __init__(self, awaitable: AwaitableType, schedule: str) -> None:
        """Create a new _CronJob.

        Creates a cron job and initiallize next scheduling with _CronJob._get_current_time as reference
        """
        log.debug(f"Create new cron with {schedule=} {awaitable=}")
        if not isinstance(schedule, str):
            raise RuntimeError("Cron format string expected to be a string")
        self.format = schedule
        self.awaitable = awaitable
        self._next_run: Optional[datetime] = None
        if schedule not in ["STARTUP", "SHUTDOWN"]:
            try:
                self.parsed = _CronStringParser(self.format)
            except InvalidCronStringException as ex:
                raise CronJobInvalid() from ex
            self._schedule(_CronJob._get_current_time())

    @property
    def months(self) -> list[int]:
        """Months on which this cron can run. Range 1-12."""
        return self.parsed.valid_months

    @property
    def weekdays(self) -> list[int]:
        """Weekdays on which this cron can run. Range 0(sun)-6(sat)."""
        return self.parsed.valid_weekdays

    @property
    def days(self) -> list[int]:
        """Days on which this cron can run. Range 1-31."""
        return self.parsed.valid_days

    @property
    def hours(self) -> list[int]:
        """Hours on which this cron can run. Range 0-23."""
        return self.parsed.valid_hours

    @property
    def minutes(self) -> list[int]:
        """Minutes on which this cron can run. Range 0-23."""
        return self.parsed.valid_minutes

    @property
    def next_run(self) -> Optional[datetime]:
        """Next point in time this cron is scheduled to run."""
        return self._next_run

    @next_run.setter
    def next_run(self, next_run: Optional[datetime]) -> None:
        self._next_run = next_run

    @next_run.deleter
    def next_run(self) -> None:
        del self._next_run

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
        """Update Job scheduling. Sets next run date in reference to the input date (e. g. now).

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
        self.next_run = next_run
        log.debug(f"next run at {next_run} ({self.due_in(current_time)}s)")

    async def run(self, now: datetime) -> None:
        """Execute a cron job.

        This function runs the cronjob and calculates the next point in time
        it needs to be schduled in reference to the input time

        Args:
            now (datetime): Time reference to calculate next scheduling.
        """
        asyncio.create_task(self.awaitable())
        self._schedule(now)

    def due_in(self, now: datetime) -> int:
        """Return seconds until the cron needs to be scheduled based on relative time input."""
        if self.next_run is None:
            raise RuntimeError(
                f"Cron {self} is not scheduled. Likely to be a STARTUP or SHUTDOWN implementation"
            )
        due_in = (self.next_run - now).total_seconds()
        return (
            int(due_in) + 1
        )  # Second precision is fine since cron operates on minutes


class CronScheduler:
    """A Cron Scheduler.

    A scheduler is a wrapper around a list of cron jobs that can be run by the main runner implementation
    """

    def __init__(self) -> None:
        """Create a new CronScheduler object used as a collection of cron jobs."""
        self.cron_startup_list: List[_CronJob] = []
        self.cron_list: List[_CronJob] = []
        self.cron_shutdown_list: List[_CronJob] = []

    def _get_next(self, now: datetime) -> Optional["_CronJob"]:
        """Return next cron job that is due for execution."""
        if not self.cron_list:
            return None
        next_cron = self.cron_list[0]
        for cron_job in self.cron_list[1:]:
            if cron_job.due_in(now) < next_cron.due_in(now):
                next_cron = cron_job
        return next_cron

    def add_cron(self, schedule: str, func: AwaitableType) -> None:
        """Add a function to be executed according to schedule.

        Args:
            schedule (str): Cron string schedule e. g. "* * * * *"
            func (AwaitableType): Awaitable that should be run accroding to schedule

        Raises:
            RuntimeWarning: _description_
        """
        cron_job = _CronJob(func, schedule)
        if inspect.signature(func).parameters:
            raise RuntimeWarning(
                f"CronJobs function with parameters are not supported rn: '{inspect.signature(func).parameters}'"
            )
        self.cron_list.append(cron_job)

    def add_startup_cron(self, func: AwaitableType) -> None:
        """Add a cron that is executed only on startup of the application."""
        cron_job = _CronJob(func, "STARTUP")
        self.cron_startup_list.append(cron_job)

    def add_shutdown_cron(self, func: AwaitableType) -> None:
        """Add a cron that is executed only on shutdown of the application."""
        cron_job = _CronJob(func, "SHUTDOWN")
        self.cron_startup_list.append(cron_job)


class Cron:
    """Main Cron runner implementation.

    A cron runner consists of a set of schedulers
    and determines which crons next to run according to their schedulers
    """

    def __init__(self) -> None:
        """Create a new cron runner instance."""
        self.schedulers: List[CronScheduler] = [CronScheduler()]

    def _get_next(self, now: datetime) -> Optional["_CronJob"]:
        """Return next cron job that is due for execution."""
        all_crons = self.get_crons()
        if not all_crons:
            return None
        next_cron = all_crons[0]
        for cron_job in all_crons[1:]:
            if cron_job.due_in(now) < next_cron.due_in(now):
                next_cron = cron_job
        return next_cron

    @property
    def scheduler(self) -> CronScheduler:
        """Return the main scheduler created in the initialization of the runner.

        Returns:
            CronScheduler: Main scheduler used for all jobs that are not added via another scheduler directly
        """
        return self.schedulers[0]

    def include_scheduler(self, scheduler: CronScheduler) -> None:
        """Add another scheduler to the cron runner implementation.

        Useful for bound methods not fully known when decorators are run. (i. e. class methods)

        Args:
            scheduler (CronScheduler): Scheduler to add. Will be included in cron execution planing
        """
        self.schedulers.append(scheduler)

    def cron(self, schedule: str) -> Callable[[AwaitableType], AwaitableType]:
        """Decorate a function function to annotate a cron function.

        Args:
            schedule (str): A valid cron format string (e. g. '0 0 1 1 0-6')

        Returns:
            Callable[[AwaitableType], AwaitableType]: The function that has been annotated
        """

        def decorator(func: AwaitableType) -> AwaitableType:
            try:
                self.scheduler.add_cron(schedule, func)

                @functools.wraps(func)
                def inner() -> Coroutine[Any, Any, None]:
                    return func()

                return inner
            except CronJobInvalid:
                log.error(
                    f"Could not setup cronjob for {func.__name__} on schedule '{schedule}'"
                )
            return func

        return decorator

    def reboot(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once on startup."""
        try:
            self.scheduler.add_startup_cron(func)
        except CronJobInvalid:
            log.error(
                f"Could not setup cronjob for {func.__name__} on '@startup' schedule"
            )
        return func

    def startup(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once on startup."""
        return self.reboot(func)

    def shutdown(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once on shutdown."""
        try:
            self.scheduler.add_shutdown_cron(func)
        except CronJobInvalid:
            log.error(
                f"Could not setup cronjob for {func.__name__} on '@shutdown' schedule"
            )
        return func

    def minutely(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job every minute."""
        return self.cron(CRON_STRING_TEMPLATE_MINUTELY)(func)

    def hourly(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once every hour."""
        return self.cron(CRON_STRING_TEMPLATE_HOURLY)(func)

    def midnight(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a day at midnight."""
        return self.cron(CRON_STRING_TEMPLATE_DAILY)(func)

    def daily(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a day at midnight."""
        return self.cron(CRON_STRING_TEMPLATE_DAILY)(func)

    def weekly(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a week at Sunday midnight."""
        return self.cron(CRON_STRING_TEMPLATE_WEEKLY)(func)

    def monthly(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a month at the 1st on midnight."""
        return self.cron(CRON_STRING_TEMPLATE_MONTHLY)(func)

    def annually(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a year on the 1st of Janurary midnight."""
        return self.cron(CRON_STRING_TEMPLATE_ANNUALLY)(func)

    def yearly(self, func: AwaitableType) -> AwaitableType:
        """Decorate a function to schedule job once a year on the 1st of Janurary midnight."""
        return self.cron(CRON_STRING_TEMPLATE_ANNUALLY)(func)

    def get_startup_crons(self) -> List[_CronJob]:
        """Return a list of all startup cronjobs included in all schedulers.

        Returns:
            List[_CronJob]: List of cron jobs run at startup
        """
        return [
            cron_job
            for scheduler in self.schedulers
            for cron_job in scheduler.cron_startup_list
        ]

    def get_shutdown_crons(self) -> List[_CronJob]:
        """Return a list of all shutdown cronjobs included in all schedulers.

        Returns:
            List[_CronJob]: List of cron jobs run at shutdown
        """
        return [
            cron_job
            for scheduler in self.schedulers
            for cron_job in scheduler.cron_shutdown_list
        ]

    def get_crons(self) -> List[_CronJob]:
        """Return a list of all periodic cronjobs included in all schedulers.

        Returns:
            List[_CronJob]: List of periodic cron jobs
        """
        return [
            cron_job
            for scheduler in self.schedulers
            for cron_job in scheduler.cron_list
        ]

    async def run_cron_async(self) -> None:
        """Run the scheduler as an asnyc function.

        Ensures the execution of discovered cronjobs and updates timinings.
        """
        for cron_job in self.get_startup_crons():
            await cron_job.awaitable()
        while True:
            now = datetime.now()
            next_cron = self._get_next(now)
            if next_cron is None:
                log.warning("No Cron could be selected for run. Exiting")
                break
            for cron_job in self.get_crons():
                if next_cron.due_in(now) >= cron_job.due_in(now):
                    log.info(
                        f"cron available in {cron_job.due_in(now)}: {cron_job.awaitable}"
                    )
            await asyncio.sleep(max(1, next_cron.due_in(now)))
            for cron_job in self.get_crons():
                now = datetime.now()
                if cron_job.next_run and now >= cron_job.next_run:
                    log.info(
                        f"{cron_job.format}: {cron_job.due_in(now)} {cron_job.next_run}"
                    )
                    await cron_job.run(now)

    def run_cron(self) -> None:
        """Run the scheduler. Ensures the execution of discovered cronjobs and updates timinings."""
        try:
            return asyncio.run(self.run_cron_async())
        except KeyboardInterrupt:
            with asyncio.Runner() as runner:
                for cron_job in self.get_shutdown_crons():
                    runner.run((cron_job.awaitable()))
            return None


if __name__ == "__main__":
    mock_dt = datetime(year=2024, month=6, day=15, hour=12, minute=13, second=0)
    logging.basicConfig()
    logging.root.setLevel(logging.DEBUG)

    async def _id() -> None:
        pass

    def _get_mock_time() -> datetime:
        return mock_dt

    # @cron("* * * * *")
    # async def cron_job_example() -> None:
    #     """Do nothhing. Used as test Cron function."""

    setattr(_CronJob, "_get_current_time", _get_mock_time)
    cron = Cron()
    FMT = "* * * * *"
    expected = datetime(year=2024, month=6, day=15, hour=12, minute=14, second=0)
    cron_next_run = _CronJob(_id, FMT).next_run
    assert cron_next_run is not None
    assert cron_next_run == expected

    log.info(f"{FMT} = {cron_next_run=} == {expected=}")
    cron.run_cron()
