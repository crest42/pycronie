.. pycronie documentation master file, created by
   sphinx-quickstart on Thu Jan 23 14:34:56 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Quickstart
==========


Install
-------

To install this package run:

``pip install pycronie``

Example
-------
To get going just annotate your first cron job with the :py:func:`cron` decorator::

   from pycronie import cron, run_cron

   @cron("* * * * *")
   async def cron_function():
      pass

   run_cron()

This will make sure that the async function `cron_function` is discovered and executed every minute by the eventloop

.. autodecorator:: pycronie.cronie.cron
