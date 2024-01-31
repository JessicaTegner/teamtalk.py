What's new
===============

This document holds a human-readable list of changes between releases.

.. note::
   teamtalk.py follows the Semantic Versioning guidelines. Releases are numbered with the following format:

    <major>.<minor>.<patch>

   And constructed with the following guidelines:

    Breaking backward compatibility bumps the major (and resets the minor and patch)
    New additions without breaking backward compatibility bumps the minor (and resets the patch)
    Bug fixes and misc changes bump the patch

    For more information on SemVer, please visit http://semver.org/.


1.2.0 - Unreleased
---------------------------------

This release adds subscriptions, and more expressive dir methods for Permissions, Channel Types and Server Properties, as well as fixing some long standing asyncio bugs. In addition, we also drop test compatibility for python 3.8

Added
~~~~~

- Added support for subscriptions. You can now subscribe to events per user and get notified when they happen. You can also unsubscribe from events.
- Added more expressive dir methods for Permissions, Channel Types and Server Properties. Now you can call dir(teamtalk.Permissions) and get a list of all permissions. Same for Channel Types and Server Properties.

Changed / Fixed
~~~~~~~~~~~~~~~

- Fixed a bug where if a registered coroutine called asyncio.sleep, the entire event loop would freeze until a new event was received.

:version:`1.1.0` - 2023-03-24
---------------------------------

Added
~~~~~

- Added the possibility to get and update TeamTalk Server properties.
- Added the possibility to create, delete, get and list user accounts.
- Added the possibility to create, update and delete channels.
- Added a teamtalk.UserAccount and teamtalk.BannedUserAccount type.
- Added a method that can list banned users.
- Added methods to get a channel from a path and a path from a channel.
- Added methods to make or remove a user as a channel operator.

Changed / Fixed
~~~~~~~~~~~~~~~

- Changed the way we check for permissions. If the bot is admin, it will have all
    permissions. If it is not, it will only have the permissions that are set
    for the bot's user account.
- Fixed the teamtalk.Instance.get_channel function so it now returns correctly.
- Fixed kicking and banning users. We now handle the case where the bot is not
    admin.
- Fixed kicking and banning users. We now handle more errors and raise when appropriate.
- Fixed a bug where it was impossible to get the server from the channel class
    when using it as part of a chain.
- Fixed a bug where it was impossible to get the server from the user class
    when using it as part of a chain.
- Fixed a bug where the sdk downloader would not work on linux, due to missing a user agent.



:version:`1.0.0` - 2023-03-01
----------------------------------

Initial release.
