API Reference
===============

The following section outlines the API of teamtalk.py.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,


Bot
--------

.. automodule:: teamtalk.bot

.. autoclass:: teamtalk.bot.TeamTalkBot
    :members:
    :exclude-members: event,dispatch

    .. automethod:: teamtalk.bot.TeamTalkBot.event()
        :decorator:


Enums
--------

.. automodule:: teamtalk.enums
    :members:


Server
--------

.. automodule:: teamtalk.server
    :members:


Channel
--------

.. automodule:: teamtalk.channel
    :members:


User
--------

.. automodule:: teamtalk.user
    :members:


Message
-----------

.. automodule:: teamtalk.message
    :members:


Audio Streaming
--------------------

.. automodule:: teamtalk.streamer
    :members:


Files
--------

.. automodule:: teamtalk.tt_file
    :members:


Permission
-------------

.. automodule:: teamtalk.permission
    :members:


Exceptions
------------

.. automodule:: teamtalk.exceptions
    :members:


TeamTalkInstance (low level)
--------------------------------

.. automodule:: teamtalk.instance
    :members:
