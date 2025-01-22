# pylint: disable=missing-module-docstring,missing-function-docstring
from datetime import datetime
from functools import partial
import pytest
from cronie.cronie import CronJob


@pytest.fixture(name="cron_job")
def cron_job_() -> partial[CronJob]:
    mock_dt = datetime(year=2024, month=6, day=15, hour=12, minute=13, second=0)

    def _get_mock_time() -> datetime:
        return mock_dt

    async def _id() -> None:
        pass

    setattr(CronJob, "_get_current_time", _get_mock_time)
    return partial(CronJob, _id)


def test_minutely(cron_job):
    assert cron_job("* * * * *").next == datetime(
        year=2024, month=6, day=15, hour=12, minute=14, second=0
    )


def test_hourly(cron_job):
    assert cron_job("0 * * * *").next == datetime(2024, 6, 15, 13, 0, 0)
    assert cron_job("13 * * * *").next == datetime(2024, 6, 15, 13, 13, 0)
    assert cron_job("14 * * * *").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("59 * * * *").next == datetime(2024, 6, 15, 12, 59, 0)


def test_daily(cron_job):
    assert cron_job("* 0 * * *").next == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* 12 * * *").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("13 12 * * *").next == datetime(2024, 6, 16, 12, 13, 0)
    assert cron_job("14 12 * * *").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* 23 * * *").next == datetime(2024, 6, 15, 23, 0, 0)
    assert cron_job("20 0 * * *").next == datetime(2024, 6, 16, 0, 20, 0)
    assert cron_job("20 20 * * *").next == datetime(2024, 6, 15, 20, 20, 0)
    assert cron_job("0 0 1 * *").next == datetime(2024, 7, 1, 0, 0, 0)
    assert cron_job("0 12 15 * *").next == datetime(2024, 7, 15, 12, 0, 0)


def test_once_a_month(cron_job):
    assert cron_job("12 12 1 * *").next == datetime(2024, 7, 1, 12, 12, 0)
    assert cron_job("* * 1 * *").next == datetime(2024, 7, 1, 0, 0, 0)
    assert cron_job("* * 30 * *").next == datetime(2024, 6, 30, 0, 0, 0)
    assert cron_job("12 12 30 * *").next == datetime(2024, 6, 30, 12, 12, 0)
    assert cron_job("15 14 1 * *").next == datetime(2024, 7, 1, 14, 15, 0)


def test_monthly(cron_job):
    assert cron_job("* * * 1 *").next == datetime(2025, 1, 1, 0, 0, 0)
    assert cron_job("* * * 12 *").next == datetime(2024, 12, 1, 0, 0, 0)


def test_fixed_datetime(cron_job):
    assert cron_job("42 23 24 12 *").next == datetime(2024, 12, 24, 23, 42, 0)
    assert cron_job("1 1 1 1 *").next == datetime(2025, 1, 1, 1, 1, 0)
    assert cron_job("0 0 1 1 *").next == datetime(2025, 1, 1, 0, 0, 0)
    assert cron_job("30 8 15 6 *").next == datetime(2025, 6, 15, 8, 30, 0)


def test_day_range(cron_job):
    assert cron_job("0 4 8-14 * *").next == datetime(2024, 7, 8, 4, 0, 0)
    assert cron_job("0 4 1-3 * *").next == datetime(2024, 7, 1, 4, 0, 0)
    assert cron_job("0 4 20-22 * *").next == datetime(2024, 6, 20, 4, 0, 0)


def test_hour_range(cron_job):
    assert cron_job("* 1-5 * * *").next == datetime(2024, 6, 16, 1, 0, 0)
    assert cron_job("* 9-17 * * *").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* 20-22 * * *").next == datetime(2024, 6, 15, 20, 0, 0)


def test_minute_range(cron_job):
    assert cron_job("5-10 * * * *").next == datetime(2024, 6, 15, 13, 5, 0)


def test_weekday(cron_job):
    assert cron_job("* * * * 1").next == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("* * * * 6").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* * * * 0").next == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* * 16 * 1").next == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* * 18 * 1").next == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("0 0 * * 0").next == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("0 0 * * 1").next == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("0 9-17 * * 1-5").next == datetime(2024, 6, 17, 9, 0, 0)
    assert cron_job("*/5 12 * * 3").next == datetime(2024, 6, 19, 12, 0, 0)
    assert cron_job("0 0 15 6 6").next == datetime(2024, 6, 22, 0, 0, 0)
    assert cron_job("0 10 1-7 * 1").next == datetime(2024, 6, 17, 10, 0, 0)
    assert cron_job("*/10 14 * * 2").next == datetime(2024, 6, 18, 14, 0, 0)


def test_fixed_time(cron_job):
    assert cron_job("5 12 * * *").next == datetime(2024, 6, 16, 12, 5, 0)
    assert cron_job("20 12 * * *").next == datetime(2024, 6, 15, 12, 20, 0)
    assert cron_job("0 0 * * *").next == datetime(2024, 6, 16, 0, 0, 0)


def test_step_minute(cron_job):
    assert cron_job("*/2 * * * *").next == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("*/15 * * * *").next == datetime(2024, 6, 15, 12, 15, 0)


def test_twice_an_hour(cron_job):
    assert cron_job("15,45 12 * * *").next == datetime(2024, 6, 15, 12, 15, 0)


def test_leap_year(cron_job):
    assert cron_job("0 0 29 2 *").next == datetime(2028, 2, 29, 0, 0, 0)
