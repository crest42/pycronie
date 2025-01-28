"""Main entry point used as example documentation and for debugging."""

# pylint: disable=missing-function-docstring,missing-module-docstring
import logging
from pycronie import Cron, CronScheduler

log = logging.getLogger(__name__)
FORMAT = "%(asctime)-15s|%(levelname)s|%(name)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

cron = Cron()


@cron.reboot
async def reboot_() -> None:
    """Run once on startup."""
    log.info(reboot_.__name__)


@cron.shutdown
async def shutdown_() -> None:
    """Run once on shutdown."""
    log.info(shutdown_.__name__)


@cron.startup
async def startup_() -> None:
    """Run once on startup."""
    log.info(startup_.__name__)


@cron.minutely
async def minutely_() -> None:
    """Run every minute."""
    log.info(minutely_.__name__)


@cron.hourly
async def hourly_() -> None:
    """Run every hour."""
    log.info(hourly_.__name__)


@cron.midnight
async def midnight_() -> None:
    """Run every day midnight."""
    log.info(midnight_.__name__)


@cron.daily
async def daily_() -> None:
    """Run once a day."""
    log.info(daily_.__name__)


@cron.weekly
async def weekly_() -> None:
    """Run once a week."""
    log.info(weekly_.__name__)


@cron.monthly
async def monthly_() -> None:
    """Run once a month."""
    log.info(monthly_.__name__)


@cron.annually
async def anually_() -> None:
    """Run once a year."""
    log.info(anually_.__name__)


@cron.yearly
async def yearly_() -> None:
    """Run once a year."""
    log.info(yearly_.__name__)


@cron.cron("* * * * *")
async def every_minute() -> None:
    """Run once every minute."""
    log.info(every_minute.__name__)


@cron.cron("*/2 * * * *")
async def every_other_minute() -> None:
    """Run once every even minute."""
    log.info(every_other_minute.__name__)


@cron.cron("0 * * * *")
async def every_hour() -> None:
    """Run once an hour at minute 0."""
    log.info(every_hour.__name__)


@cron.cron("50 * * * *")
async def every_hour2() -> None:
    """Run once an hour at minute 50."""
    log.info(every_hour2.__name__)


@cron.cron("* 2 * * *")
async def mornig() -> None:
    """Run every monrning at 2 am."""
    log.info(mornig.__name__)


@cron.cron("* 20 * * *")
async def night() -> None:
    """Run every night at 8 pm."""
    log.info(night.__name__)


@cron.cron("0 0 * * *")
async def midnight__() -> None:
    """Run every night at midnight."""
    log.info(midnight__.__name__)


@cron.cron("0 12 * * *")
async def noon() -> None:
    """Run every day at noon."""
    log.info(noon.__name__)


@cron.cron("0 0 1 * *")
async def fom() -> None:
    """Run on first of month."""
    log.info(fom.__name__)


@cron.cron("0 0 30 * *")
async def lom() -> None:
    """Run on last of month on the 30st."""
    log.info(lom.__name__)


@cron.cron("0 0 31 * *")
async def lom2() -> None:
    """Run on last of month if the last of the month is a 31st."""
    log.info(lom2.__name__)


@cron.cron("0 0 1 1 *")
async def jan() -> None:
    """Run on the first of Janurary once."""
    log.info(jan.__name__)


@cron.cron("0 0 1 12 *")
async def dec() -> None:
    """Run in december once."""
    log.info(dec.__name__)


@cron.cron("0 0 24 12 *")
async def christmas() -> None:
    """Run on Christmas."""
    log.info(christmas.__name__)


@cron.cron("0 12 21 1 *")
async def all_set() -> None:
    """Run once on Janurary."""
    log.info(all_set.__name__)


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


if __name__ == "__main__":
    test_class = TestClass()
    cron.include_scheduler(test_class.scheduler)
    cron.run_cron()
