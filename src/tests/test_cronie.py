# pylint: disable=missing-module-docstring,missing-function-docstring
from datetime import datetime
from functools import partial
import pytest
from pycronie import CronJob, CronJobInvalid


@pytest.fixture(name="cron_job")
def cron_job_() -> partial[CronJob]:
    mock_dt = datetime(year=2024, month=6, day=15, hour=12, minute=13, second=0)

    def _get_mock_time() -> datetime:
        return mock_dt

    async def _id() -> None:
        pass

    setattr(CronJob, "_get_current_time", _get_mock_time)
    return partial(CronJob, _id)


def test_minutely(cron_job: partial[CronJob]) -> None:
    assert cron_job("* * * * *").next_run == datetime(
        year=2024, month=6, day=15, hour=12, minute=14, second=0
    )


def test_once(cron_job: partial[CronJob]) -> None:
    assert cron_job("STARTUP").next_run is None
    assert cron_job("SHUTDOWN").next_run is None


def test_hourly(cron_job: partial[CronJob]) -> None:
    assert cron_job("0 * * * *").next_run == datetime(2024, 6, 15, 13, 0, 0)
    assert cron_job("13 * * * *").next_run == datetime(2024, 6, 15, 13, 13, 0)
    assert cron_job("14 * * * *").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("59 * * * *").next_run == datetime(2024, 6, 15, 12, 59, 0)


def test_daily(cron_job: partial[CronJob]) -> None:
    assert cron_job("* 0 * * *").next_run == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* 12 * * *").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("13 12 * * *").next_run == datetime(2024, 6, 16, 12, 13, 0)
    assert cron_job("14 12 * * *").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* 23 * * *").next_run == datetime(2024, 6, 15, 23, 0, 0)
    assert cron_job("20 0 * * *").next_run == datetime(2024, 6, 16, 0, 20, 0)
    assert cron_job("20 20 * * *").next_run == datetime(2024, 6, 15, 20, 20, 0)
    assert cron_job("0 0 1 * *").next_run == datetime(2024, 7, 1, 0, 0, 0)
    assert cron_job("0 12 15 * *").next_run == datetime(2024, 7, 15, 12, 0, 0)


def test_once_a_month(cron_job: partial[CronJob]) -> None:
    assert cron_job("12 12 1 * *").next_run == datetime(2024, 7, 1, 12, 12, 0)
    assert cron_job("* * 1 * *").next_run == datetime(2024, 7, 1, 0, 0, 0)
    assert cron_job("* * 30 * *").next_run == datetime(2024, 6, 30, 0, 0, 0)
    assert cron_job("12 12 30 * *").next_run == datetime(2024, 6, 30, 12, 12, 0)
    assert cron_job("15 14 1 * *").next_run == datetime(2024, 7, 1, 14, 15, 0)


def test_monthly(cron_job: partial[CronJob]) -> None:
    assert cron_job("* * * 1 *").next_run == datetime(2025, 1, 1, 0, 0, 0)
    assert cron_job("* * * 12 *").next_run == datetime(2024, 12, 1, 0, 0, 0)


def test_fixed_datetime(cron_job: partial[CronJob]) -> None:
    assert cron_job("42 23 24 12 *").next_run == datetime(2024, 12, 24, 23, 42, 0)
    assert cron_job("1 1 1 1 *").next_run == datetime(2025, 1, 1, 1, 1, 0)
    assert cron_job("0 0 1 1 *").next_run == datetime(2025, 1, 1, 0, 0, 0)
    assert cron_job("30 8 15 6 *").next_run == datetime(2025, 6, 15, 8, 30, 0)


def test_day_range(cron_job: partial[CronJob]) -> None:
    assert cron_job("0 4 8-14 * *").next_run == datetime(2024, 7, 8, 4, 0, 0)
    assert cron_job("0 4 1-3 * *").next_run == datetime(2024, 7, 1, 4, 0, 0)
    assert cron_job("0 4 20-22 * *").next_run == datetime(2024, 6, 20, 4, 0, 0)


def test_hour_range(cron_job: partial[CronJob]) -> None:
    assert cron_job("* 1-5 * * *").next_run == datetime(2024, 6, 16, 1, 0, 0)
    assert cron_job("* 9-17 * * *").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* 20-22 * * *").next_run == datetime(2024, 6, 15, 20, 0, 0)


def test_minute_range(cron_job: partial[CronJob]) -> None:
    assert cron_job("5-10 * * * *").next_run == datetime(2024, 6, 15, 13, 5, 0)


def test_invalid_strings(cron_job: partial[CronJob]) -> None:
    with pytest.raises(CronJobInvalid):
        cron_job("/5 * * * *")
        cron_job("* y * * *")
        cron_job(" * * *")
        cron_job("*")
        cron_job("1-90 * * * *")
        cron_job("* * * * foo")
        cron_job("-1 * * * *")
        cron_job("* * * * -1")
        cron_job("* * * -1 *")
        cron_job("* * -1 * *")
        cron_job("* -1 * * *")
        cron_job("-1 * * * *")
        cron_job("* * * * 8")
        cron_job("* * * 13 *")
        cron_job("* * 32 * *")
        cron_job("* 25 * * *")
        cron_job("61 * * * *")
        cron_job("* * 0 * *")
        cron_job("* * * 0 *")

        # Thanks GPT
        cron_job("* * *")  # Missing two fields (should have 5 fields)
        cron_job("* * * * * *")  # Too many fields (should have 5 fields)
        cron_job("*/0 * * * *")  # Invalid step value (step cannot be 0)
        cron_job("-5 * * * *")  # Negative value in minute field
        cron_job("61 * * * *")  # Out-of-range minute (valid: 0-59)
        cron_job("0 24 * * *")  # Out-of-range hour (valid: 0-23)
        cron_job("0 * 32 * *")  # Out-of-range day of month (valid: 1-31)
        cron_job("0 * 0 * *")  # Invalid day of month (valid: 1-31)
        cron_job("0 * * 13 *")  # Out-of-range month (valid: 1-12)
        cron_job("0 * * 0 *")  # Invalid month (valid: 1-12)
        cron_job(
            "0 * * * 8"
        )  # Out-of-range day of week (valid: 0-7, where 0 and 7 both mean Sunday)
        cron_job("0 * * * -1")  # Negative day of week
        cron_job("* */25 * * *")  # Invalid step for hour (valid: 1-23)
        cron_job("* * 1-31/0 * *")  # Invalid step for day of month (step cannot be 0)
        cron_job("*/60 * * * *")  # Step larger than the valid range for minutes
        cron_job(
            "0 0 * Jan-Mar *"
        )  # Invalid month format (should use numeric values or abbreviations like JAN, FEB)
        cron_job(
            "0 0 * * Sun-Mon"
        )  # Invalid day of week format (should use numeric values or abbreviations like SUN, MON)
        cron_job(
            "*/5 10 * ? *"
        )  # Question mark (`?`) is not standard for all cron systems
        cron_job(
            "0 0 L * *"
        )  # `L` is not universally supported (last day of the month is specific to extended cron implementations)
        cron_job("0 0 1W * *")  # `1W` (nearest weekday) is not supported by all parsers


def test_minute_step(cron_job: partial[CronJob]) -> None:
    assert cron_job("*/5 * * * *").next_run == datetime(2024, 6, 15, 12, 15, 0)
    assert cron_job("5-20/5 * * * *").next_run == datetime(2024, 6, 15, 12, 15, 0)


def test_weekday(cron_job: partial[CronJob]) -> None:
    assert cron_job("* * * * 1").next_run == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("* * * * 6").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* * * * 0").next_run == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* * 16 * 1").next_run == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("* * 18 * 1").next_run == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("0 0 * * 0").next_run == datetime(2024, 6, 16, 0, 0, 0)
    assert cron_job("0 0 * * 1").next_run == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("0 9-17 * * 1-5").next_run == datetime(2024, 6, 17, 9, 0, 0)
    assert cron_job("*/5 12 * * 3").next_run == datetime(2024, 6, 19, 12, 0, 0)
    assert cron_job("0 0 15 6 6").next_run == datetime(2024, 6, 22, 0, 0, 0)
    assert cron_job("0 10 1-7 * 1").next_run == datetime(2024, 6, 17, 10, 0, 0)
    assert cron_job("*/10 14 * * 2").next_run == datetime(2024, 6, 18, 14, 0, 0)
    assert cron_job("* * * * 1/2").next_run == datetime(2024, 6, 17, 0, 0, 0)
    assert cron_job("* * * * 2/2").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("* * * * 5/3").next_run == datetime(2024, 6, 21, 0, 0, 0)
    assert cron_job("* * * * 2/3").next_run == datetime(2024, 6, 18, 0, 0, 0)


def test_fixed_time(cron_job: partial[CronJob]) -> None:
    assert cron_job("5 12 * * *").next_run == datetime(2024, 6, 16, 12, 5, 0)
    assert cron_job("20 12 * * *").next_run == datetime(2024, 6, 15, 12, 20, 0)
    assert cron_job("0 0 * * *").next_run == datetime(2024, 6, 16, 0, 0, 0)


def test_step_minute(cron_job: partial[CronJob]) -> None:
    assert cron_job("*/2 * * * *").next_run == datetime(2024, 6, 15, 12, 14, 0)
    assert cron_job("*/15 * * * *").next_run == datetime(2024, 6, 15, 12, 15, 0)


def test_twice_an_hour(cron_job: partial[CronJob]) -> None:
    assert cron_job("15,45 12 * * *").next_run == datetime(2024, 6, 15, 12, 15, 0)


def test_leap_year(cron_job: partial[CronJob]) -> None:
    assert cron_job("0 0 29 2 *").next_run == datetime(2028, 2, 29, 0, 0, 0)
