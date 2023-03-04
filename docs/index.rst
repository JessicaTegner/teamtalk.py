Welcome to the TeamTalk.py Documentation
========================================

teamtalk.py is a Python library that provides a simple interface to connect to, and interact with, TeamTalk servers.


Installation
------------

To install teamtalk.py, simply run the following command:

.. code-block::

    pip install teamtalk.py

Alternatively, you can download the source code from the GitHub repository and run the following command:

.. code-block::

    git clone https://github.com/JessicaTegner/teamtalk.py.git
    cd teamtalk.py
    poetry build
    pip install dist/teamtalk.py-*.tar.gz


Quick Start
-----------

To quickly get started with teamtalk.py, you can use the following code snippet:

.. code-block::

    import teamtalk

    # Create a new TeamTalk bot
    bot = teamtalk.Bot()

    # listen to some events
    @bot.event
    def on_ready():
        print("Bot is ready!")

    @bot.event
    def on_message(message):
        print(f"Received message: {message}")

    # then add our servers
    bot.add_server("localhost", 10333, 10333, "serveradmin", "password")

    # and finally, connect to the servers and start listening for events
    bot.run()


Useful Links
------------

Below are some useful links to help you get started with teamtalk.py:

* :doc:`event reference </events>`
* :doc:`API Documentation </api>`
* :doc:`whats-new </whats-new>`
* `GitHub Repository <https://github.com/JessicaTegner/teamtalk.py>`_
* `PyPI <https://pypi.org/project/teamtalk.py/>`_


Contributing
------------

So you want to contribute to teamtalk.py? Great! There are many ways to contribute to this project, and all contributions are welcome.

If you have found a bug, have a feature request or want to help improve documentation please `open an issue <https://https://github.com/jessicaTegner/issues/new>`_

You can also donate to the projects maintainer (JessicaTegner) in the following way to help support the development of teamtalk.py:

* `GitHub Sponsors <https://github.com/sponsors/JessicaTegner>`_
* `PayPal <https://paypal.me/JessicaTegner>`_


License
-------

teamtalk.py is licensed under the MIT License. See the `LICENSE <https://github.com/JessicaTegner/teamtalk.py/blob/master/LICENSE>`_ file for more information.

.. |PyPI| image:: https://img.shields.io/pypi/v/teamtalk.py.svg
   :target: https://pypi.org/project/teamtalk.py/
   :alt: PyPI
