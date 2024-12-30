"""Channel module for teamtalk.py."""

from typing import List, Union

from ._utils import _get_tt_obj_attribute, _set_tt_obj_attribute, _waitForCmd
from .permission import Permission
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
            self._channel, self.path = self.teamtalk._get_channel_info(self.id)

        # if the channel is a sdk.Channel, set it to self._channel
        elif isinstance(channel, sdk.Channel):
            self._channel = channel
            self.id = channel.nChannelID
            self._channel, self.path = self.teamtalk._get_channel_info(self.id)
        self.server = self.teamtalk.server


    def update(self) -> bool:
        """Update the channel information.

        Example:
            >>> channel = teamtalk.get_channel(1)
            >>> channel.name = "New Channel Name"
            >>> channel.update()

        Raises:
            PermissionError: If the bot does not have permission to update the channel.
            ValueError: If the channel could not be updated.

        Returns:
            bool: True if the channel was updated successfully.
        """
        if not self.teamtalk.has_permission(Permission.MODIFY_CHANNELS) or not sdk._IsChannelOperator(
            self._tt, self.super.getMyUserID(), self.id
        ):
            raise PermissionError("the bot does not have permission to update the channel.")
        result = sdk._DoUpdateChannel(self.teamtalk._tt, self._channel)
        if result == -1:
            raise ValueError("Channel could not be updated")
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to update channels")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                raise ValueError("Channel could not be found")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_ALREADY_EXISTS:
                raise ValueError("Channel already exists")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_HAS_USERS:
                raise ValueError("Channel has users and can therefore not be updated")
        return True

    def _refresh(self) -> None:
        self._channel, self.path = self.teamtalk._get_channel_info(self.id)

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
        msg.szMessage = sdk.ttstr(content)
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

    def subscribe(self, subscription) -> None:
        """Subscribe to a subscription for all users in this channel.

        Args:
            subscription: The subscription to subscribe to.
        """
        users = self.get_users()
        for user in users:
            user.subscribe(subscription)

    def unsubscribe(self, subscription) -> None:
        """Unsubscribe from a subscription for all users in this channel.

        Args:
            subscription: The subscription to unsubscribe from.
        """
        users = self.get_users()
        for user in users:
            user.unsubscribe(subscription)

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

    def __setattr__(self, name: str, value):
        """Try to set the specified attribute.

        Args:
            name: The name of the attribute.
            value: The value to set the attribute to.

        Raises:
            AttributeError: If the specified attribute is not found. This is the default behavior. # noqa
        """
        if name in dir(self):
            self.__dict__[name] = value
        else:
            # id cannot be change.
            if name in ["teamtalk", "id", "server", "path", "_channel"]:
                self.__dict__[name] = value
            else:
                _get_tt_obj_attribute(self._channel, name)
                # if we have gotten here, we can set the attribute
                _set_tt_obj_attribute(self._channel, name, value)


class _ChannelTypeMeta(type):
    def __getattr__(cls, name: str) -> sdk.UserRight:
        name = f"CHANNEL_{name}"
        return getattr(sdk.ChannelType, name, None)

    def __dir__(cls) -> list[str]:
        return [attr[8:] for attr in dir(sdk.ChannelType) if attr.startswith("CHANNEL_")]


class ChannelType(metaclass=_ChannelTypeMeta):
    """A class representing Channel types in TeamTalk."""