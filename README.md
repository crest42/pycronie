# pycronie

This is a small python project to schedule python function as cron like jobs, using a decorator syntax.

Currently only async function are executed as part of an asyncio event loop.

## Installing

To install this project use

> pip install pycronie

## Example

To schedule a async function one must import the cron decorator and use it on any async function:

```
from pycronie import cron

@cron("* * * * *")
async def cron_function():
    pass
```

To run the eventloop use run_cron():

```
crom pycronie import run_cron

run_cron()
```