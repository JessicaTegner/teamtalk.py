"""This module contains the TeamTalkInstance class.

The TeamTalkInstance class contains one instance of a connection to a TeamTalkServer.
It is used to send and receive messages, join and leave channels, and perform other actions.
In addition, it's also here that events are dispatched.
"""

import os
import logging
import time
import ctypes
from typing import List, Union

from ._utils import _getAbsTimeDiff, _waitForEvent, _do_after
from .channel import Channel as TeamTalkChannel
from .enums import TeamTalkServerInfo, UserStatusMode
from .exceptions import PermissionError
from .implementation.TeamTalkPy import TeamTalk5 as sdk
from .message import BroadcastMessage, ChannelMessage, CustomMessage, DirectMessage
from .permission import Permission
from .server import Server as TeamTalkServer
from .tt_file import RemoteFile
from .user import User as TeamTalkUser


_log = logging.getLogger(__name__)


class TeamTalkInstance(sdk.TeamTalk):
    """Represents a TeamTalk5 instance."""

    def __init__(self, bot, server_info: TeamTalkServerInfo) -> None:
        """Initializes a teamtalk.TeamTalkInstance instance.

        Args:
            bot: The teamtalk.Bot instance.
            server_info: The server info for the server we wish to connect to.
        """
        # put the super class in a variable so we can call it later
        self.super = super()
        # call the super class's __init__ method
        self.super.__init__()
        # set the bot
        self.bot = bot
        # set the server info
        self.server_info = server_info
        self.server = TeamTalkServer(self, server_info)
        self.channel = lambda self: self.get_channel(self.super.getMyChannelID())
        self.connected = False
        self.logged_in = False
        self.init_time = time.time()

    def connect(self) -> bool:
        """Connects to the server. This doesn't return until the connection is successful or fails.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        if not self.super.connect(
            sdk.ttstr(self.server_info.host),
            self.server_info.tcp_port,
            self.server_info.udp_port,
            self.server_info.encrypted,
        ):
            return False
        result, msg = _waitForEvent(self.super, sdk.ClientEvent.CLIENTEVENT_CON_SUCCESS)
        if not result:
            return False
        self.bot.dispatch("my_connect", self.server)
        self.connected = True
        self.init_time = time.time()
        return True

    def login(self, join_channel_on_login: bool = True) -> bool:
        """Logs in to the server. This doesn't return until the login is successful or fails.

        Args:
            join_channel_on_login: Whether to join the channel on login or not.

        Returns:
            bool: True if the login was successful, False otherwise.
        """
        self.super.doLogin(
            sdk.ttstr(self.server_info.nickname),
            sdk.ttstr(self.server_info.username),
            sdk.ttstr(self.server_info.password),
            sdk.ttstr(self.bot.client_name),
        )
        result, msg = _waitForEvent(self.super, sdk.ClientEvent.CLIENTEVENT_CMD_MYSELF_LOGGEDIN)
        if not result:
            return False
        self.bot.dispatch("my_login", self.server)
        self.logged_in = True
        if join_channel_on_login:
            channel_id = self.server_info.join_channel_id
            if channel_id < 1:
                channel_id = self.super.getRootChannelID()
            self.join_channel_by_id(channel_id)
        self.init_time = time.time()
        return True

    def logout(self):
        """Logs out of the server."""
        self.super.doLogout()
        self.logged_in = False

    def disconnect(self):
        """Disconnects from the server."""
        self.super.disconnect()
        self.connected = False

    def change_nickname(self, nickname: str):
        """Changes the nickname of the bot.

        Args:
            nickname: The new nickname.
        """
        self.super.doChangeNickname(nickname)

    def change_status(self, status_mode: UserStatusMode, status_message: str):
        """Changes the status of the bot.

        Args:
            status_mode: The status mode.
            status_message: The status message.
        """
        self.super.doChangeStatus(status_mode, status_message)

    # permission stuff
    def has_permission(self, permission: Permission) -> bool:
        """Checks if the bot has a permission.

        Args:
            permission: The permission to check for.

        Returns:
            bool: True if the bot has the permission, False otherwise.
        """
        user = self.super.getMyUserAccount()
        user_rights = user.uUserRights
        return (user_rights & permission) == permission

    def is_admin(self) -> bool:
        """Checks if the bot is an admin.

        Returns:
            bool: True if the bot is an admin, False otherwise.
        """
        return self.is_user_admin(self.super.getMyUserID())

    def is_user_admin(self, user: Union[TeamTalkUser, int]) -> bool:
        """Checks if a user is an admin.

        Args:
            user: The user to check.

        Returns:
            bool: True if the user is an admin, False otherwise.

        Raises:
            TypeError: If the user is not of type teamtalk.User or int.
        """
        if isinstance(user, int):
            user = self.super.getUser(user)
            return user.uUserType == sdk.UserType.USERTYPE_ADMIN
        if isinstance(user, TeamTalkUser):
            return user.user_type == sdk.UserType.USERTYPE_ADMIN
        raise TypeError("User must be of type teamtalk.User or int")

    def join_root_channel(self):
        """Joins the root channel."""
        self.join_channel_by_id(self.super.getRootChannelID())

    def join_channel_by_id(self, id: int, password: str = ""):
        """Joins a channel by its ID.

        Args:
            id: The ID of the channel to join.
            password: The password of the channel to join.
        """
        self.super.doJoinChannelByID(id, sdk.ttstr(password))

    def join_channel(self, channel: TeamTalkChannel):
        """Joins a channel.

        Args:
            channel: The channel to join.
        """
        self.super.doJoinChannelByID(channel.id, sdk.ttstr(channel.password))

    def leave_channel(self):
        """Leaves the current channel."""
        self.super.doLeaveChannel()

    def get_channel(self, channel_id: int) -> TeamTalkChannel:
        """Gets a channel by its ID.

        Args:
            channel_id: The ID of the channel to get.

        Returns:
            TeamTalkChannel: The channel.
        """
        return self.bot, TeamTalkChannel(self, channel_id)

    def get_user(self, user_id: int) -> TeamTalkUser:
        """Gets a user by its ID.

        Args:
            user_id: The ID of the user to get.

        Returns:
            TeamTalkUser: The user.
        """
        return TeamTalkUser(self, user_id)

    # file stuff
    def upload_file(self, channel_id: int, filepath: str) -> None:
        """Uploads a local file to a channel.

        Args:
            channel_id: The ID of the channel to upload the file to.
            filepath: The path to the local file to upload.

        Raises:
            PermissionError: If the bot does not have permission to upload files.
            ValueError: If the channel ID is less than 0.
            FileNotFoundError: If the local file does not exist.
        """
        if not self.has_permission(Permission.UPLOAD_FILES):
            raise PermissionError("You do not have permission to upload files")
        if channel_id < 0:
            raise ValueError("Channel ID must be greater than 0")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
        self.super.doSendFile(channel_id, sdk.ttstr(filepath))

    def download_file(self, channel_id: int, remote_file_name: str, local_file_path: str) -> None:
        """Downloads a remote file from a channel.

        Args:
            channel_id: The ID of the channel to download the file from.
            remote_file_name: The name of the remote file to download.
            local_file_path: The path to save the file to.

        Raises:
            PermissionError: If the bot does not have permission to download files.
            ValueError: If the channel ID is less than 0.
        """
        if not self.has_permission(Permission.DOWNLOAD_FILES):
            raise PermissionError("You do not have permission to download files")
        if channel_id < 0:
            raise ValueError("Channel ID must be greater than 0")
        remote_files = self.get_channel_files(channel_id)
        # loop through files and print the name
        for file in remote_files:
            if file.file_name == remote_file_name:
                self.download_file_by_id(channel_id, file.file_id, local_file_path)

    def download_file_by_id(self, channel_id: int, file_id: int, filepath: str):
        """Downloads a remote file from a channel by its ID.

        Args:
            channel_id: The ID of the channel to download the file from.
            file_id: The ID of the file to download.
            filepath: The path to save the file to.

        Raises:
            PermissionError: If the bot does not have permission to download files.
        """
        if not self.has_permission(Permission.DOWNLOAD_FILES):
            raise PermissionError("You do not have permission to download files")
        self.super.doRecvFile(channel_id, file_id, sdk.ttstr(filepath))

    def delete_file_by_id(self, channel_id: int, file_id: int):
        """Deletes a remote file from a channel by its ID.

        Args:
            channel_id: The ID of the channel to delete the file from.
            file_id: The ID of the file to delete.

        Raises:
            PermissionError: If the bot does not have permission to delete files.
        """
        if not self.is_admin(self.super.getMyUserID()):
            raise PermissionError("You do not have permission to delete files")
        self.super.doDeleteFile(channel_id, file_id)

    def get_channel_files(self, channel_id: int) -> List[RemoteFile]:
        """Gets a list of remote files in a channel.

        Args:
            channel_id: The ID of the channel to get the files from.

        Returns:
            List[RemoteFile]: A list of remote files in the channel.
        """
        files = self.super.getChannelFiles(channel_id)
        return [RemoteFile(self, file) for file in files]

    def move_user(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int]) -> None:
        """Moves a user to a channel.

        Args:
            user: The user to move.
            channel: The channel to move the user to.

        Raises:
            PermissionError: If the bot does not have permission to move users.
            TypeError: If the user or channel is not a subclass of User or Channel.
        """
        if not self.has_permission(Permission.MOVE_USERS):
            raise PermissionError("You do not have permission to move users")
        _log.debug(f"Moving user {user} to channel {channel}")
        self._do_cmd(user, channel, "_DoMoveUser")

    def kick_user(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int]) -> None:
        """Kicks a user from a channel or the server.

        Args:
            user: The user to kick.
            channel: The channel to kick the user from. If 0, the user will be kicked from the server. # noqa

        Raises:
            PermissionError: If the bot does not have permission to kick users.
            TypeError: If the user or channel is not a subclass of User or Channel.
        """
        if not self.has_permission(Permission.KICK_USERS):
            raise PermissionError("You do not have permission to kick users")
        _log.debug(f"Kicking user {user} from channel {channel}")
        self._do_cmd(user, channel, "_DoKickUser")

    def ban_user(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int]) -> None:
        """Bans a user from a channel or the server.

        Args:
            user: The user to ban.
            channel: The channel to ban the user from. If 0, the user will be banned from the server. # noqa

        Raises:
            PermissionError: If the bot does not have permission to ban users.
            TypeError: If the user or channel is not a subclass of User or Channel.
        """
        if not self.has_permission(Permission.BAN_USERS):
            raise PermissionError("You do not have permission to ban users")
        _log.debug(f"Banning user {user} from channel {channel}")
        self._do_cmd(user, channel, "_DoBanUser")

    def unban_user(self, ip: str, channel: Union[TeamTalkChannel, int]) -> None:
        """Unbans a user from the server.

        Args:
            ip: The IP address of the user to unban.
            channel: The channel to unban the user from. If 0, the user will be unbanned from the server. # noqa

        Raises:
            PermissionError: If the bot does not have permission to unban users.
        """
        if not self.has_permission(Permission.UNBAN_USERS):
            raise PermissionError("You do not have permission to unban users")
        if not isinstance(ip, str):
            raise TypeError("IP must be a string")
        if not isinstance(channel, (TeamTalkChannel, int)):
            raise TypeError("Channel must be a subclass of Channel or a channel ID")
        channel_id = channel
        if isinstance(channel, TeamTalkChannel):
            channel_id = channel.id
        _log.debug(f"Unbanning user {ip}")
        sdk._DoUnBanUser(self._tt, sdk.ttstr(ip), channel_id)

    def _send_message(self, message: sdk.TextMessage, **kwargs):
        """Sends a message.

        Args:
            message: The message to send.
            delay: The delay in seconds before sending the message. Defaults to 0 which means no delay. # noqa
            **kwargs: Keyword arguments. Reserved for future use.


        Raises:
            TypeError: If the message is not a subclass of Message.
        """
        if not isinstance(message, sdk.TextMessage):
            raise TypeError("Message must be a subclass of sdk.TextMessage")
        if not issubclass(type(message), sdk.TextMessage):
            raise TypeError("Message must be a subclass of sdk.TextMessage")
        delay = kwargs.get("delay", 0)
        _do_after(delay, lambda: self.super.doTextMessage(ctypes.POINTER(sdk.TextMessage)(message)))

    async def _process_events(self) -> None:  # noqa: C901
        """Processes events from the server. This is automatically called by teamtalk.Bot."""
        msg = self.super.getMessage()
        event = msg.nClientEvent
        if event != sdk.ClientEvent.CLIENTEVENT_NONE and _getAbsTimeDiff(self.init_time, time.time()) < 1500:
            # done so we don't get random events when logging in
            return
        if event == sdk.ClientEvent.CLIENTEVENT_NONE:
            return
        if event == sdk.ClientEvent.CLIENTEVENT_USER_AUDIOBLOCK:
            self.bot.dispatch("user_audio", self, msg)
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_TEXTMSG:
            message = None
            if msg.textmessage.nMsgType == sdk.TextMsgType.MSGTYPE_USER:
                message = DirectMessage(self, msg.textmessage)
            elif msg.textmessage.nMsgType == sdk.TextMsgType.MSGTYPE_CHANNEL:
                message = ChannelMessage(self, msg.textmessage)
            elif msg.textmessage.nMsgType == sdk.TextMsgType.MSGTYPE_BROADCAST:
                message = BroadcastMessage(self, msg.textmessage)
            elif msg.textmessage.nMsgType == sdk.TextMsgType.MSGTYPE_CUSTOM:
                message = CustomMessage(self, msg.textmessage)
            if message:
                self.bot.dispatch("message", message)
                return
            # user events
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_LOGGEDIN:
            self.bot.dispatch("user_login", TeamTalkUser(self, msg.user))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_LOGGEDOUT:
            self.bot.dispatch("user_logout", TeamTalkUser(self, msg.user))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_UPDATE:
            self.bot.dispatch("user_update", TeamTalkUser(self, msg.user))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_JOINED:
            user = TeamTalkUser(self, msg.user)
            self.bot.dispatch("user_join", user, user.channel)
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USER_LEFT:
            user = TeamTalkUser(self, msg.user)
            self.bot.dispatch("user_left", user, TeamTalkChannel(self, msg.nSource))
            return
        # channel events
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_CHANNEL_NEW:
            self.bot.dispatch("channel_new", TeamTalkChannel(self, msg.channel))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_CHANNEL_UPDATE:
            self.bot.dispatch("channel_update", TeamTalkChannel(self, msg.channel))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_CHANNEL_REMOVE:
            self.bot.dispatch("channel_delete", TeamTalkChannel(self, msg.channel))
            return
        # server events
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_SERVER_UPDATE:
            self.bot.dispatch("server_update", self.server)
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_SERVERSTATISTICS:
            self.bot.dispatch("server_statistics", self.server)
            return
        # FILE EVENTS
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_FILE_NEW:
            self.bot.dispatch("file_new", RemoteFile(self, msg.remotefile))
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_FILE_REMOVE:
            self.bot.dispatch("file_delete", RemoteFile(self, msg.remotefile))
            return
        # other "my" events
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_MYSELF_KICKED:
            self.bot.dispatch("my_kicked_from_channel", TeamTalkChannel(self, msg.nSource))
            return

    def _get_channel_info(self, channel_id: int):
        _channel = self.getChannel(channel_id)
        _channel_path = self.getChannelPath(channel_id)
        return _channel, _channel_path

    def _get_my_permissions(self):
        return self.super._GetMyUserRights()

    def _do_cmd(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int], func) -> None:
        if not self.has_permission(Permission.KICK_USERS):
            raise PermissionError("You do not have permission to kick users")
        if not isinstance(user, (TeamTalkUser, int)):
            raise TypeError("User must be a teamtalk.User or a user id")
        if not isinstance(channel, (TeamTalkChannel, int)):
            raise TypeError("Channel must be a teamtalk.Channel or a channel id")
        user_id = user
        if isinstance(user, TeamTalkUser):
            user_id = user.user_id
        channel_id = channel
        if isinstance(channel, TeamTalkChannel):
            channel_id = channel.id
        sdk_func = getattr(sdk, func)
        sdk_func(self._tt, user_id, channel_id)
