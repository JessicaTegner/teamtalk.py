"""A module that contains the TeamTalkBot class.

The TeamTalkBot class is the main class of the library.
It's used to create a bot,connect to any amount of TeamTalk servers and dispatch events.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from .enums import TeamTalkServerInfo
from .instance import TeamTalkInstance

T = TypeVar("T")
Coro = Coroutine[Any, Any, T]
CoroT = TypeVar("CoroT", bound=Callable[..., Coro[Any]])


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        msg = "loop attribute cannot be accessed in non-async contexts. "
        raise AttributeError(msg)


_loop: Any = _LoopSentinel()
_log = logging.getLogger(__name__)


class TeamTalkBot:
    """A class that represents a TeamTalk bot."""

    def __init__(self, client_name: Optional[str] = "Teamtalk.py") -> None:
        """Initialize a TeamTalkBot object.

        Args:
            client_name (Optional[str]): The name of the client. Defaults to "Teamtalk.py".
        """
        self.client_name = client_name
        self.loop: asyncio.AbstractEventLoop = _loop
        # hold a list of TeamTalk instances
        self.teamtalks: List[TeamTalkInstance] = []
        self._listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}

    async def add_server(self, server: Union[TeamTalkServerInfo, dict]) -> None:
        """Add a server to the bot.

        Args:
            server: A Union[TeamTalkServerInfo, dict] object representing the server to add.
                If a dictionary is provided, it will be converted to a TeamTalkServerInfo object.
        """
        if isinstance(server, dict):
            server = TeamTalkServerInfo.from_dict(server)
        _log.debug(f"Adding server: {self, server}")
        tt = TeamTalkInstance(self, server)
        # connect
        tt.connect()
        # login
        tt.login()
        self.teamtalks.append(tt)

    def run(self):
        """A blocking call that connects to all added servers and handles all events."""

        async def runner():
            async with self:
                await self._start()

        # setup logging to log debug messages
        # and log everyhting to console
        logging.basicConfig(level=logging.DEBUG)

        try:
            # set our loop the asyncio event loop
            asyncio.run(runner())
        except KeyboardInterrupt:
            # nothing to do here
            # `asyncio.run` handles the loop cleanup
            # and `self.start` closes all sockets and the HTTPClient instance.
            return

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop

    async def __aenter__(self) -> Self:
        """A context manager that is used to get the correct event loop.

        Returns:
            Self: The TeamTalkBot object.
        """
        await self._async_setup_hook()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback,
    ) -> None:
        """When we exit the program, try to disconnect from all servers.

        Args:
            exc_type (Optional[Type[BaseException]]): The exception type.
            exc_value (Optional[BaseException]): The exception value.
            traceback: The traceback.
        """
        for teamtalk in self.teamtalks:
            teamtalk.disconnect()
            teamtalk.closeTeamTalk()

    def event(self, coro: CoroT, /) -> CoroT:
        """A decorator that registers an event to listen to.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        ---------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')


        See the :doc:`event Reference </events>` for more information and a list of all events.


        Args:
            coro (CoroT): The coroutine to register.

        Returns:
            CoroT: The coroutine that was registered.

        Raises:
            TypeError: The coroutine is not a coroutine function.
        """
        _log.debug("Registering event %s", coro.__name__)

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("event registered must be a coroutine function")

        setattr(self, coro.__name__, coro)
        _log.debug("Registered event %s", coro.__name__)
        return coro

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            _log.debug("Running event %s", event_name)
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            _log.debug("Event %s was cancelled", event_name)
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        # print all the events to log
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return self.loop.create_task(wrapped, name=f"teamtalk.py: {event_name}")

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        """|coro| .

        The default error handler provided by the client.

        By default this logs to the library logger however it could be
        overridden to have a different implementation.
        The traceback from this exception is logged to the logging module.

        Args:
            event_method (str): The event method that errored.
            *args (Any): The arguments to the event.
            **kwargs (Any): The keyword arguments to the event.
        """
        _log.exception("Ignoring exception in %s", event_method)

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        """Dispatch an event to all listeners. This is called internally.

        Args:
            event (str): The name of the event to dispatch.
            *args (Any): The arguments to the event.
            **kwargs (Any): The keyword arguments to the event.
        """
        _log.debug("Dispatching event %s", event)
        method = "on_" + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def _start(self):
        self.dispatch("ready")
        # make a while loop and allow it to run forever
        try:
            while True:
                # loop through the teamtalks and check  for events
                for teamtalk in self.teamtalks:
                    await teamtalk._process_events()
                await asyncio.sleep(0.001)
        except KeyboardInterrupt:
            # try to disconnect everything cleanly
            for teamtalk in self.teamtalks:
                # disconnect from the server
                teamtalk.doLogout()
                self.dispatch("my_logout", teamtalk.server)
                teamtalk.disconnect()
                self.dispatch("my_disconnect", teamtalk.server)

    async def _do_after_delay(self, delay, func, *args, **kwargs):
        await asyncio.sleep(delay)
        print("WORKS")
