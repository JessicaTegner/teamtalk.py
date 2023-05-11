"""Provides the Server class for interacting with a TeamTalk5 server."""

import ctypes
from typing import Union

from ._utils import _get_tt_obj_attribute, _set_tt_obj_attribute
from .permission import Permission
from .channel import Channel as TeamTalkChannel
from .exceptions import PermissionError
from .implementation.TeamTalkPy import TeamTalk5 as sdk
from .user import User as TeamTalkUser


class Server:
    """Represents a TeamTalk5 server.

    Attributes:
        teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
        info: The server information.
    """

    def __init__(self, teamtalk_instance, server_info):
        """Initializes a Server instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            server_info: The server information.
        """
        self.teamtalk_instance = teamtalk_instance
        self.info = server_info

    def send_message(self, content: str, **kwargs):
        """Sends a message to all users on the server, using a broadcast message.

        Args:
            content: The content of the message.
            **kwargs: Keyword arguments. See teamtalk.TeamTalkInstance.send_message for more information.

        Returns:
            The result of the doTextMessage call.

        Raises:
            PermissionError: If the user is not an admin.
        """
        if not self.teamtalk_instance.is_admin():
            raise PermissionError("You must be an admin to send messages to the server")
        msg = sdk.TextMessage()
        msg.nMsgType = sdk.TextMsgType.MSGTYPE_BROADCAST
        msg.nFromUserID = self.teamtalk_instance.getMyUserID()
        msg.szFromUsername = self.teamtalk_instance.getMyUserAccount().szUsername
        msg.nToUserID = 0
        msg.szMessage = content
        msg.bMore = False
        # get a pointer to our message
        return self.teamtalk_instance._send_message(msg, **kwargs)

    def ping(self) -> bool:
        """Pings the server.

        Returns:
            True if the ping is successful, False otherwise.
        """
        return self.teamtalk_instance.super._DoPing(self.info.nServerPort)

    def get_users(self) -> list:
        """Gets a list of users on the server.

        Returns:
            A list of teamtalk.User instances representing the users on the server.
        """
        users = self.teamtalk_instance.super.getServerUsers()
        return [TeamTalkUser(self.teamtalk_instance, user) for user in users]

    def get_channels(self) -> list:
        """Gets a list of channels on the server.

        Returns:
            A list of teamtalk.Channel instances representing the channels on the server.
        """
        channels = self.teamtalk_instance.super.getServerChannels()
        return [TeamTalkChannel(self.teamtalk_instance, channel) for channel in channels]

    def get_channel(self, channel_id):
        """Gets the channel with the specified ID.

        Args:
            channel_id: The ID of the channel.

        Returns:
            The teamtalk.Channel instance representing the channel with the specified ID.
        """
        channel = self.teamtalk_instance.super.getChannel(channel_id)
        return TeamTalkChannel(self.teamtalk_instance, channel)

    def get_user(self, user_id):
        """Gets the user with the specified ID.

        Args:
            user_id: The ID of the user.

        Returns:
            The teamtalk.User instance representing the user with the specified ID.
        """
        user = self.teamtalk_instance.super.getUser(user_id)
        return TeamTalkUser(self.teamtalk_instance, user)

    def move_user(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int]):
        """Moves the specified user to the specified channel.

        Args:
            user: The user to move.
            channel: The channel to move the user to.

        Raises:
            PermissionError: If the user is not an admin.
        """
        if not self.teamtalk_instance.is_admin():
            raise PermissionError("You must be an admin to move users")
        if isinstance(user, TeamTalkUser):
            user = user.id
        if isinstance(channel, TeamTalkChannel):
            channel = channel.id
        self.teamtalk_instance.move_user(user, channel)

    def kick(self, user: Union[TeamTalkUser, int]):
        """Kicks the specified user from the specified channel.

        Args:
            user: The user to kick.

        Raises:
            PermissionError: If the user is not an admin.
        """
        self.teamtalk_instance.kick_user(user, 0)

    def ban(self, user: Union[TeamTalkUser, int]):
        """Bans the specified user from the specified channel.

        Args:
            user: The user to ban.

        Raises:
            PermissionError: If the user is not an admin.
        """
        self.teamtalk_instance.ban_user(user, 0)

    def unban(self, user: Union[TeamTalkUser, int]):
        """Unbans the specified user from the specified channel.

        Args:
            user: The user to unban.

        Raises:
            PermissionError: If the user is not an admin.
        """
        self.teamtalk_instance.unban_user(user, 0)

    def subscribe(self, subscription):
        """Subscribes to the specified subscription for all users on the server.

        Args:
            subscription: The subscription to subscribe to.

        """
        users = self.get_users()
        for user in users:
            user.subscribe(subscription)

    def unsubscribe(self, subscription):
        """Unsubscribes to the specified subscription for all users on the server.

        Args:
            subscription: The subscription to unsubscribe to.

        """
        users = self.get_users()
        for user in users:
            user.unsubscribe(subscription)

    def get_properties(self) -> "ServerProperties":
        """Gets the properties of the server.

        Returns:
            A teamtalk.ServerProperties instance representing the properties of the server.
        """
        props = self.teamtalk_instance.super.getServerProperties()
        return ServerProperties(self.teamtalk_instance, props)

    def update_properties(self, properties: "ServerProperties"):
        """Updates the properties of the server.

        Args:
            properties: The updated properties. See teamtalk.ServerProperties for more information.

        Raises:
            PermissionError: If the bot does not have the permission to update the properties.
        """
        if not self.teamtalk_instance.has_permission(Permission.UPDATE_SERVERPROPERTIES):
            raise PermissionError("The bot does not have permission to update the server properties")
        # get the underlying properties object
        properties = properties.properties
        sdk._DoUpdateServer(self.teamtalk_instance._tt, ctypes.byref(properties))

    def __getattr__(self, name: str):
        """Try to get the specified attribute on server.

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
            return _get_tt_obj_attribute(self._user, name)


class ServerProperties(object):
    """Represents the properties of a server.

    This class should not be instantiated directly. Instead, use the teamtalk.Server.get_properties() method. # noqa

    Example:
        >>> server = teamtalk server
        >>> properties = server.get_properties()
        >>> properties.max_users
        1000
        >>> properties.max_users = 500
        >>> server.update_properties(properties)
        >>> properties = server.get_properties()
        >>> properties.max_users
        500
    """

    def __init__(self, teamtalk_instance, properties):
        """Initializes a new instance of the ServerProperties class.

        Args:
            teamtalk_instance: The teamtalk.TeamTalk instance.
            properties: The underlying properties object.
        """
        self.teamtalk_instance = teamtalk_instance
        self.properties = properties

    def __getattr__(self, name: str):
        """Try to get the specified attribute on server.

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
            return _get_tt_obj_attribute(self.properties, name)

    def __setattr__(self, name: str, value):
        """Try to set the specified attribute on properties.

        Args:
            name: The name of the attribute.
            value: The value to set the attribute to.

            Raises:
                AttributeError: If the specified attribute is not found.
        """
        if name in dir(self):
            self.__dict__[name] = value
        else:
            # if name is either teamtalk_instance or properties, just set it on self
            if name in ["teamtalk_instance", "properties"]:
                self.__dict__[name] = value
            else:
                _get_tt_obj_attribute(self.properties, name)
                # if we have gotten here, we can set the attribute
                _set_tt_obj_attribute(self.properties, name, value)
