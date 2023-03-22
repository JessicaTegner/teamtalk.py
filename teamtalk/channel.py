"""Channel module for teamtalk.py."""

from typing import List, Union

from ._utils import _get_tt_obj_attribute
from .exceptions import PermissionError
from .implementation.TeamTalkPy import TeamTalk5 as sdk
from .tt_file import RemoteFile
from .user import User as TeamTalkUser


class Channel:
    """Represents a channel on a TeamTalk server."""

    def __init__(self, teamtalk, channel: Union[int, sdk.Channel]) -> None:
        """Initialize a Channel object.

        Args:
            teamtalk: The teamtalk.TeamTalkInstance instance.
            channel (Union[int, sdk.Channel]): The channel ID or a sdk.Channel object.
        """
        self.teamtalk = teamtalk
        # if the channel_id is a int, set it to the channel_id
        if isinstance(channel, int):
            self.id = channel
            self._refresh()
        # if the channel is a sdk.Channel, set it to self._channel
        elif isinstance(channel, sdk.Channel):
            self._channel = channel
            self.id = channel.nChannelID
            self.channel_path = channel.szName
        self.server = self.teamtalk.server

    def _refresh(self) -> None:
        self._channel, self.channel_path = self.teamtalk._get_channel_info(self.id)

    def send_message(self, content: str, **kwargs) -> None:
        """Send a message to the channel.

        Args:
            content: The message to send.
            **kwargs: Keyword arguments. See teamtalk.TeamTalkInstance.send_message for more information.

        Raises:
            PermissionError: If the bot is not in the channel and is not an admin.
        """
        # get the bots current channel id with getMyChannelID
        # if the bots current channel id is not the same as the channel id we are trying to send a message to, return
        if self.teamtalk.getMyChannelID() != self.id:
            if not self.teamtalk.is_admin():
                raise PermissionError("Missing permission to send message to channel that the bot is not in")
        msg = sdk.TextMessage()
        msg.nMsgType = sdk.TextMsgType.MSGTYPE_CHANNEL
        msg.nFromUserID = self.teamtalk.getMyUserID()
        msg.szFromUsername = self.teamtalk.getMyUserAccount().szUsername
        msg.nChannelID = self.id
        msg.szMessage = content
        msg.bMore = False
        # get a pointer to our message
        self.teamtalk._send_message(msg, **kwargs)

    def upload_file(self, filepath):
        """Upload a file to the channel.

        Args:
            filepath (str): The local path to the file to upload.
        """
        self.teamtalk.upload_file(self.id, filepath)

    def get_users(self) -> List[TeamTalkUser]:
        """Get a list of users in the channel.

        Returns:
            List[TeamTalkUser]: A list of teamtalk.User instances in the channel.
        """
        users = self.teamtalk.super.getChannelUsers(self.id)
        return [TeamTalkUser(self.teamtalk, user) for user in users]

    def get_files(self) -> List[RemoteFile]:
        """Get a list of files in the channel.

        Returns:
            List[RemoteFile]: A list of teamtalk.RemoteFile instances in the channel.
        """
        files = self.teamtalk.super.getChannelFiles(self.id)
        return [RemoteFile(self.teamtalk, f) for f in files]

    def move(self, user: Union[TeamTalkUser, int]) -> None:
        """Move a user to this channel.

        Args:
            user: The user to move.
        """
        self.teamtalk.move_user(user, self, False)

    def kick(self, user: Union[TeamTalkUser, int]) -> None:
        """Kick a user from this channel.

        Args:
            user: The user to kick.
        """
        self.teamtalk.kick_user(user, self)

    def ban(self, user: Union[TeamTalkUser, int]) -> None:
        """Ban a user from this channel.

        Args:
            user: The user to ban.
        """
        self.teamtalk.ban_user(user, self)

    def __getattr__(self, name: str):
        """Try to get the attribute from the channel object.

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
            return _get_tt_obj_attribute(self._channel, name)


class _ChannelTypeMeta(type):
    def __getattr__(cls, name: str) -> sdk.UserRight:
        name = f"CHANNEL_{name}"
        return getattr(sdk.ChannelType, name, None)


class ChannelType(metaclass=_ChannelTypeMeta):
    """A class representing user permissions in TeamTalk."""
