# pylint: disable=missing-function-docstring,missing-module-docstring
import logging
from cronie.cronie import (
    cron, run_cron, reboot, startup,
    shutdown, minutely, hourly, midnight,
    daily, weekly, monthly, annually, yearly
)
log = logging.getLogger(__name__)
FORMAT = "%(asctime)-15s|%(levelname)s|%(name)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

@reboot
async def reboot_() -> None:
    log.info(reboot_.__name__)

@shutdown
async def shutdown_() -> None:
    log.info(shutdown_.__name__)

@startup
async def startup_() -> None:
    log.info(startup_.__name__)

@minutely
async def minutely_() -> None:
    log.info(minutely_.__name__)

@hourly
async def hourly_() -> None:
    log.info(hourly_.__name__)

@midnight
async def midnight_() -> None:
    log.info(midnight_.__name__)

@daily
async def daily_() -> None:
    log.info(daily_.__name__)

@weekly
async def weekly_() -> None:
    log.info(weekly_.__name__)


@monthly
async def monthly_() -> None:
    log.info(monthly_.__name__)

@annually
async def anually_() -> None:
    log.info(anually_.__name__)

@yearly
async def yearly_() -> None:
    log.info(yearly_.__name__)


@cron("* * * * *")
async def every_minute() -> None:
    log.info(every_minute.__name__)


@cron("*/2 * * * *")
async def every_other_minute() -> None:
    log.info(every_other_minute.__name__)


@cron("0 * * * *")
async def every_hour() -> None:
    log.info(every_hour.__name__)


@cron("50 * * * *")
async def every_hour2() -> None:
    log.info(every_hour2.__name__)


@cron("* 2 * * *")
async def mornig() -> None:
    log.info(mornig.__name__)


@cron("* 20 * * *")
async def night() -> None:
    log.info(night.__name__)


@cron("0 0 * * *")
async def midnight__() -> None:
    log.info(midnight__.__name__)


@cron("0 12 * * *")
async def noon() -> None:
    log.info(noon.__name__)


@cron("0 0 1 * *")
async def fom() -> None:
    log.info(fom.__name__)


@cron("0 0 30 * *")
async def lom() -> None:
    log.info(lom.__name__)


@cron("0 0 31 * *")
async def lom2() -> None:
    log.info(lom2.__name__)


@cron("0 0 1 1 *")
async def jan() -> None:
    log.info(jan.__name__)


@cron("0 0 1 12 *")
async def dec() -> None:
    log.info(dec.__name__)


@cron("0 0 24 12 *")
async def christmas() -> None:
    log.info(christmas.__name__)


@cron("0 12 21 1 *")
async def all_set() -> None:
    log.info(all_set.__name__)


if __name__ == "__main__":
    run_cron()
