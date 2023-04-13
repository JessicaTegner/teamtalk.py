"""This module contains the Message class and its subclasses."""


from .implementation.TeamTalkPy import TeamTalk5 as sdk


class Message:
    """Represents a TeamTalk5 message. This class should not be instantiated directly."""

    def __init__(self, teamtalk_instance, msg):
        """Initializes a Message instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            msg: The message.
        """
        self.teamtalk_instance = teamtalk_instance
        self.type = msg.nMsgType
        self.from_id = msg.nFromUserID
        self.to_id = msg.nToUserID
        self.content = msg.szMessage
        # if content is a byte array, decode it
        if isinstance(self.content, bytes):
            self.content = self.content.decode("utf-8")
        self.user = self.teamtalk_instance.get_user(self.from_id)

    def reply(self, content, **kwargs):
        """Replies to the message.

        The reply will be sent to the place where the message was sent from.
        Meaning that if the message was sent to a channel, the reply will be sent to the channel.
        If the message was sent to a user, the reply will be sent to the user.
        And if the message was a broadcast message, the reply will be sent to the server as a broadcast.

        Args:
            content: The content of the message.
            **kwargs: Keyword arguments. See teamtalk.TeamTalkInstance.send_message for more information.

        Returns:
            The message ID of the reply.

        Raises:
            PermissionError: If the sender doesn't have permission to send the message.
        """
        msg = sdk.TextMessage()
        msg.nMsgType = self.type
        msg.nFromUserID = self.teamtalk_instance.super.getMyUserID()
        msg.szFromUsername = self.teamtalk_instance.super.getMyUserAccount().szUsername
        # if self is channel message, then reply to channel
        if isinstance(self, ChannelMessage):
            if self.teamtalk_instance.super.getMyChannelID() != self.to_id:
                if not self.teamtalk_instance.is_admin():
                    raise PermissionError("You don't have permission to send messages across channels.")
            msg.nChannelID = self.to_id
        if isinstance(self, BroadcastMessage):
            # if we aren ot admin we cant do this
            if not self.teamtalk_instance.is_admin():
                raise PermissionError("You don't have permission to send broadcast messages.")
            msg.nToUserID = 0
            msg.nChannelID = 0
        else:
            msg.nToUserID = self.from_id
        msg.szMessage = sdk.ttstr(content)
        msg.bMore = False
        return self.teamtalk_instance._send_message(msg, **kwargs)

    def is_me(self) -> bool:
        """Checks if the message was sent by the bot.

        Returns:
            True if the message was sent by the bot, False otherwise.
        """
        return self.from_id == self.teamtalk_instance.super.getMyUserID()

    def __str__(self) -> str:
        """Returns a string representation of the message.

        Returns:
            A string representation of the message.
        """
        return f"teamtalk.{type(self).__name__}(from_id={self.from_id}, to_id={self.to_id}, content={self.content})"


# make a channel message subclass
class ChannelMessage(Message):
    """Represents a message sent to a channel. This class should not be instantiated directly."""

    def __init__(self, teamtalk_instance, msg):
        """Initializes a ChannelMessage instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            msg: The message payload.
        """
        super().__init__(teamtalk_instance, msg)
        self.to_id = msg.nChannelID
        self.channel_id = msg.nChannelID
        self.channel = self.teamtalk_instance.get_channel(self.channel_id)


class DirectMessage(Message):
    """Represents a message sent to a user. This class should not be instantiated directly."""

    def __init__(self, teamtalk_instance, msg):
        """Initializes a DirectMessage instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            msg: The message payload.
        """
        super().__init__(teamtalk_instance, msg)
        self.to_id = msg.nToUserID
        # if the id is still 0, then it's a private message to the bot
        if self.to_id == 0:
            self.to_id = teamtalk_instance.getMyUserID()


class BroadcastMessage(Message):
    """Represents a message sent to a server. This class should not be instantiated directly."""

    def __init__(self, teamtalk_instance, msg):
        """Initializes a BroadcastMessage instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            msg: The message payload.
        """
        super().__init__(teamtalk_instance, msg)


class CustomMessage(Message):
    """Represents a custom message. This class should not be instantiated directly."""

    def __init__(self, teamtalk_instance, msg):
        """Initializes a CustomMessage instance.

        Args:
            teamtalk_instance: An instance of teamtalk.TeamTalkInstance.
            msg: The message payload.
        """
        super().__init__(teamtalk_instance, msg)
