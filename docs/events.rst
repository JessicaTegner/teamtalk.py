event reference
==================

This page documents the various events that a TeamTalk Bot can listen to.

The tables are grouped by relevance.

For more information, on what each teamtalk.* function does, please refer to the :doc:`/api` documentation.


How do I use these events?
----------------------------

The events are listed in the following tables. Each event has a name, a list of arguments that are passed to the event handler and a description of what the event is.

To listen to an event, you must use the :func:`teamtalk.bot.event` decorator.


example:

.. code-block:: python

    @bot.event
    def on_message(message):
        print(message)


The above code will print the message object to the console whenever a message is sent. The message object is passed to the event handler as an argument.


Missellaneous Events
-----------------------


.. csv-table:: Missellaneous Events
   :delim: \u0009
   :header: "name", "Argument(s)", "Description"
   :file: _static/csv/miss.csv


Bot Events
-------------

.. csv-table:: Bot Events
   :delim: \u0009
   :header: "name", "Argument(s)", "Description"
   :file: _static/csv/bot.csv

Server, Channel & File Events
--------------------------------------

.. csv-table:: Server, Channel & File Events
   :delim: \u0009
   :header: "name", "Argument(s)", "Description"
   :file: _static/csv/server_channel_n_file.csv


User Events
--------------

.. csv-table:: User Events
   :delim: \u0009
   :header: "name", "Argument(s)", "Description"
   :file: _static/csv/user.csv
