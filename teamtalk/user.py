"""This module defines a User class that represents a user on a TeamTalk server."""

# Union type
from typing import Union

from ._utils import _get_tt_obj_attribute
from .implementation.TeamTalkPy import TeamTalk5 as sdk


class User:
    """Represents a user on a TeamTalk server.

    Attributes:
        teamtalk_instance: An instance of TeamTalk.TeamTalkInstance.
        user: Either a string (username) or an int (user_id) or an instance of sdk.User.
    """

    def __init__(self, teamtalk_instance, user: Union[str, int, sdk.User]):
        """Initializes the User instance.

        Args:
            teamtalk_instance: An instance of TeamTalk5.
            user: Either a string (username) or an int (user_id) or an instance of sdk.User.

        Raises:
            TypeError: If the user argument is not of the expected type.
        """
        self.teamtalk_instance = teamtalk_instance
        # if user is str, assume it's a username
        if isinstance(user, str):
            self._user = self.teamtalk_instance.super.getUserByUsername(user)
        # if user is int, assume it's a user_id
        elif isinstance(user, int):
            self._user = self.teamtalk_instance.super.getUser(user)
        # if the user argument is already of type sdk.User, just set it to self._user
        elif isinstance(user, sdk.User):
            self._user = user
        else:
            raise TypeError(f"user must be either a string or an int. Argument has type: {str(type(user))}.")
        self.id = self.user_id
        self.channel = self.teamtalk_instance.get_channel(self._user.nChannelID)
        self.server = self.channel.server

    def send_message(self, content: str, **kwargs) -> int:
        """Sends a text message to this user.

        Args:
            content: The content of the message.
            **kwargs: Keyword arguments. See teamtalk.TeamTalkInstance.send_message for more information.

        Returns:
            The ID of the message if successful, or a negative value if unsuccessful.
        """
        msg = sdk.TextMessage()
        msg.nMsgType = sdk.TextMsgType.MSGTYPE_USER
        msg.nFromUserID = self.teamtalk_instance.getMyUserID()
        msg.szFromUsername = self.teamtalk_instance.getMyUserAccount().szUsername
        msg.nToUserID = self.user_id
        msg.szMessage = content
        msg.bMore = False
        # get a pointer to our message
        return self.teamtalk_instance._send_message(msg, **kwargs)

    def move(self, channel) -> bool:
        """Moves this user to the specified channel.

        Args:
            channel: The channel to move this user to.

        Returns:
            True if the user was moved successfully, False otherwise.
        """
        return self.server.move_user(self, channel)

    def kick(self, from_server: bool) -> None:
        """Kicks this user from the server.

        Args:
            from_server: If True, the user will be kicked from the server. If False, the user will be kicked from the channel. # noqa
        """
        channel_id = 0
        if not from_server:
            channel_id = self.channel.id
        self.teamtalk_instance.kick_user(self, channel_id)

    def ban(self, from_server: bool) -> None:
        """Bans this user from the server.

        Args:
            from_server: If True, the user will be banned from the server. If False, the user will be banned from the channel. # noqa
        """
        channel_id = 0
        if not from_server:
            channel_id = self.channel.id
        self.teamtalk_instance.ban_user(self, channel_id)

    def subscribe(self, subscription) -> None:
        """Subscribes to the specified subscription.

        Args:
            subscription: The subscription to subscribe to.
        """
        self.teamtalk_instance.subscribe(self, subscription)

    def unsubscribe(self, subscription) -> None:
        """Unsubscribes from the specified subscription.

        Args:
            subscription: The subscription to unsubscribe from.
        """
        self.teamtalk_instance.unsubscribe(self, subscription)

    def is_subscribed(self, subscription) -> bool:
        """Checks if this user is subscribed to the specified subscription.

        Args:
            subscription: The subscription to check.

        Returns:
            True if the bot is subscribed to the specified subscription from this user, False otherwise.
        """
        return self.teamtalk_instance.is_subscribed(self, subscription)

    def __getattr__(self, name: str):
        """Try to get the specified attribute from self._user if it is not found in self.

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
