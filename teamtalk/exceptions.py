"""teamtalk.py exceptions."""


class TeamTalkException(Exception):
    """Base exception class for teamtalk.py.

    All other exceptions inherit from this class, which inherits from :exc:`Exception`.
    """

    def __init__(self, message: str) -> None:
        """Initialise the exception.

        Args:
            message (str): The message to be displayed when the exception is raised.
        """
        super().__init__(message)


class PermissionError(TeamTalkException):
    """Exception raised when the bot does not have permission to perform an action."""
