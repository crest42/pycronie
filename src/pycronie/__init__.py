"""Cronie is a python library to schedule python functions as cron like jobs, using decorators.

To schedule a async function use::

    from pycronie import Cron
    cron = Cron()
    @cron.cron("* * * * *")
    async def cron_function():
        pass

    cron.run_cron()

This will register cron_function to be scheduled each minute.
Calling run_cron ensures the cron event loop is executed.

The algorithm used reflects that of unix cron where:

- For each job the next execution time is calculated
- Sleep seconds until the next job(s) is up for execution
- Execute all jobs that are up for execution
- Repeat

"""

from pycronie.cronie import (
    Cron,
    CronJobInvalid,
    CronScheduler,
    CronCache,
    VoidInputArg,
)

__all__ = [
    "CronJobInvalid",
    "Cron",
    "CronScheduler",
    "CronCache",
    "VoidInputArg",
]
