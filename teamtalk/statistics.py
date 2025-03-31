"""Server statistics module for Teamtalk."""

from .implementation.TeamTalkPy import TeamTalk5 as sdk
from ._utils import _get_tt_obj_attribute


class Statistics:
    """represents the statistics of a TeamTalk server."""

    def __init__(self, teamtalk, statistics: sdk.ServerStatistics) -> None:
        """
        Initialize a statistics object.

        Args:
            teamtalk: The teamtalk.TeamTalkInstance instance.
            statistics (sdk.ServerStatistics): The sdk.ServerStatistics object.
        """
        self.teamtalk = teamtalk
        self.server = teamtalk.server
        self._statistics = statistics

    def __getattr__(self, name: str):
        """Try to get the attribute from the ServerStatistics object.

        Args:
            name: The name of the attribute.

        Returns:
            The value of the specified attribute.

        Raises:
            AttributeError: If the specified attribute is not found. This is the default behavior. # noqa
        """
        if name in dir(self):
            return self.__dict__[name]
        else:
            return _get_tt_obj_attribute(self._statistics, name)

    def refresh(self):
        """Refreshes The servers statistics."""
        self = self.teamtalk.get_server_statistics()
