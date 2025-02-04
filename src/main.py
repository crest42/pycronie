"""Main entry point used as example documentation and for debugging."""

# pylint: disable=missing-function-docstring,missing-module-docstring
import logging
from pycronie import Cron, CronScheduler, CronCache, VoidInputArg

log = logging.getLogger(__name__)
FORMAT = "%(asctime)-15s|%(levelname)s|%(name)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

cron = Cron()


@cron.reboot
async def reboot_() -> None:
    """Run once on startup."""
    log.info(reboot_)


@cron.shutdown
async def shutdown_() -> None:
    """Run once on shutdown."""
    log.info(shutdown_)


@cron.startup
async def startup_() -> None:
    """Run once on startup."""
    log.info(startup_)


@cron.minutely
async def minutely_() -> None:
    """Run every minute."""
    log.info(minutely_)


@cron.hourly
async def hourly_() -> None:
    """Run every hour."""
    log.info(hourly_)


@cron.midnight
async def midnight_() -> None:
    """Run every day midnight."""
    log.info(midnight_)


@cron.daily
async def daily_() -> None:
    """Run once a day."""
    log.info(daily_)


@cron.weekly
async def weekly_() -> None:
    """Run once a week."""
    log.info(weekly_)


@cron.monthly
async def monthly_() -> None:
    """Run once a month."""
    log.info(monthly_)


@cron.annually
async def anually_() -> None:
    """Run once a year."""
    log.info(anually_)


@cron.yearly
async def yearly_() -> None:
    """Run once a year."""
    log.info(yearly_)


@cron.cron("* * * * *")
async def every_minute() -> None:
    """Run once every minute."""
    log.info(every_minute)


@cron.cron("*/2 * * * *")
async def every_other_minute() -> None:
    """Run once every even minute."""
    log.info(every_other_minute)


@cron.cron("0 * * * *")
async def every_hour() -> None:
    """Run once an hour at minute 0."""
    log.info(every_hour)


@cron.cron("50 * * * *")
async def every_hour2() -> None:
    """Run once an hour at minute 50."""
    log.info(every_hour2)


@cron.cron("* 2 * * *")
async def mornig() -> None:
    """Run every monrning at 2 am."""
    log.info(mornig)


@cron.cron("* 20 * * *")
async def night() -> None:
    """Run every night at 8 pm."""
    log.info(night)


@cron.cron("0 0 * * *")
async def midnight__() -> None:
    """Run every night at midnight."""
    log.info(midnight__)


@cron.cron("0 12 * * *")
async def noon() -> None:
    """Run every day at noon."""
    log.info(noon)


@cron.cron("0 0 1 * *")
async def fom() -> None:
    """Run on first of month."""
    log.info(fom)


@cron.cron("0 0 30 * *")
async def lom() -> None:
    """Run on last of month on the 30st."""
    log.info(lom)


@cron.cron("0 0 31 * *")
async def lom2() -> None:
    """Run on last of month if the last of the month is a 31st."""
    log.info(lom2)


@cron.cron("0 0 1 1 *")
async def jan() -> None:
    """Run on the first of Janurary once."""
    log.info(jan)


@cron.cron("0 0 1 12 *")
async def dec() -> None:
    """Run in december once."""
    log.info(dec)


@cron.cron("0 0 24 12 *")
async def christmas() -> None:
    """Run on Christmas."""
    log.info(christmas)


@cron.cron("0 12 21 1 *")
async def all_set() -> None:
    """Run once on Janurary."""
    log.info(all_set)


@cron.cron("* * 31 2,4,6,9,11 *")
async def invalid_day_of_month() -> None:
    """Only run on even months on day 31 -> impossible."""


@cron.cron("* * * * *")
async def all_set_with_arg(cache: CronCache) -> None:
    """Run minutely with cache."""
    if not cache.foo:
        cache.foo = 1
    else:
        cache.foo += 1
    log.info(f"all_set_with_arg: {cache.foo}")


@cron.cron("* * * * *")
async def all_set_with_arg2(cache: CronCache, void: VoidInputArg) -> None:
    """Run minutely with cache and void arg."""
    if not cache.foo:
        cache.foo = 1
    else:
        cache.foo += 1
    log.info(f"all_set_with_arg2: {cache.foo} {void}")


@cron.minutely
async def all_set_with_arg_minutely(cache: CronCache) -> None:
    """Run minutely with cache."""
    if not cache.foo:
        cache.foo = 1
    else:
        cache.foo += 1
    log.info(f"all_set_with_arg_minutely: {cache.foo}")


class TestClass:
    """Test class for cusomter scheduler inclusion."""

    def __init__(self) -> None:
        """Create Test object."""
        self.it = 0
        self.scheduler = CronScheduler()
        self.scheduler.add_cron("* * * * *", self.minutely)

    async def minutely(
        self,
    ) -> None:
        """Test Cron."""
        print(f"Run it {self.it}")
        self.it += 1


@cron.startup
async def valid_arg(cache: CronCache) -> None:
    """Run every minute."""
    if cache.run is None:
        cache.run = 1
    else:
        cache.run += 1
    log.info(f"{valid_arg}: {cache.run}")


@cron.startup
async def valid_arg2(cache: CronCache, void: VoidInputArg) -> None:
    """Run every minute."""
    if cache.run is None:
        cache.run = 1
    else:
        cache.run += 1
    log.info(f"{valid_arg}: {cache.run} {void}")


@cron.startup
async def valid_arg3(void: VoidInputArg, cache: CronCache) -> None:
    """Run every minute."""
    if cache.run is None:
        cache.run = 1
    else:
        cache.run += 1
    log.info(f"{valid_arg}: {cache.run} {void}")


if __name__ == "__main__":
    test_class = TestClass()
    cron.include_scheduler(test_class.scheduler)
    cron.run_cron()
