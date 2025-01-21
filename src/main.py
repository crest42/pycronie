# pylint: disable=missing-function-docstring,missing-module-docstring
from cronie.cronie import (
    cron, run_cron, reboot, startup,
    shutdown, minutely, hourly, midnight,
    daily, weekly, monthly, annually, yearly
)

@reboot
async def reboot_() -> None:
    print(reboot_.__name__)

@shutdown
async def shutdown_() -> None:
    print(shutdown_.__name__)

@startup
async def startup_() -> None:
    print(startup_.__name__)

@minutely
async def minutely_() -> None:
    print(minutely_.__name__)

@hourly
async def hourly_() -> None:
    print(hourly_.__name__)

@midnight
async def midnight_() -> None:
    print(midnight_.__name__)

@daily
async def daily_() -> None:
    print(daily_.__name__)

@weekly
async def weekly_() -> None:
    print(weekly_.__name__)


@monthly
async def monthly_() -> None:
    print(monthly_.__name__)

@annually
async def anually_() -> None:
    print(anually_.__name__)

@yearly
async def yearly_() -> None:
    print(yearly_.__name__)


@cron("* * * * *")
async def every_minute() -> None:
    print(every_minute.__name__)


@cron("*/2 * * * *")
async def every_other_minute() -> None:
    print(every_other_minute.__name__)


@cron("0 * * * *")
async def every_hour() -> None:
    print(every_hour.__name__)


@cron("50 * * * *")
async def every_hour2() -> None:
    print(every_hour2.__name__)


@cron("* 2 * * *")
async def mornig() -> None:
    print(mornig.__name__)


@cron("* 20 * * *")
async def night() -> None:
    print(night.__name__)


@cron("0 0 * * *")
async def midnight__() -> None:
    print(midnight__.__name__)


@cron("0 12 * * *")
async def noon() -> None:
    print(noon.__name__)


@cron("0 0 1 * *")
async def fom() -> None:
    print(fom.__name__)


@cron("0 0 30 * *")
async def lom() -> None:
    print(lom.__name__)


@cron("0 0 31 * *")
async def lom2() -> None:
    print(lom2.__name__)


@cron("0 0 1 1 *")
async def jan() -> None:
    print(jan.__name__)


@cron("0 0 1 12 *")
async def dec() -> None:
    print(dec.__name__)


@cron("0 0 24 12 *")
async def christmas() -> None:
    print(christmas.__name__)


@cron("0 12 21 1 *")
async def all_set() -> None:
    print(all_set.__name__)


if __name__ == "__main__":
    import logging
    log = logging.getLogger(__name__)
    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")
    log.debug("foo")
    run_cron()
