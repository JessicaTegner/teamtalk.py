"""Teamtalk file object."""

from ._utils import _get_tt_obj_attribute


class RemoteFile:
    """Represents a file on a TeamTalk server. Should not be instantiated directly."""

    def __init__(self, teamtalk_instance, payload):
        """Initializes the RemoteFile instance.

        Args:
            teamtalk_instance: The teamtalk.TeamTalkInstance instance.
            payload: An instance of sdk.RemoteFile.
        """
        self.teamtalk = teamtalk_instance
        self.channel = lambda self: self.teamtalk.get_channel(payload.nChannelID)
        self.server = lambda self: self.teamtalk.server
        self.payload = payload

    def __str__(self) -> str:
        """Returns a string representation of the RemoteFile instance.

        Returns:
            A string representation of the RemoteFile instance.
        """
        return f"Teamtalk.RemoteFile(file_name={self.file_name}, file_id={self.file_id}, file_size={self.file_size}, username={self.username}, upload_time={self.upload_time})"  # noqa: E501

    def __getattr__(self, name: str):
        """Returns the value of the specified attribute of the remote file.

        Args:
            name: The name of the attribute.

        Returns:
            The value of the specified attribute.

        Raises:
            AttributeError: If the specified attribute is not found. # noqa
        """
        if name in dir(self):
            return self.__dict__[name]
        else:
            return _get_tt_obj_attribute(self.payload, name)
