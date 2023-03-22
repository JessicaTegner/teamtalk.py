"""This module contains the TeamTalkInstance class.

The TeamTalkInstance class contains one instance of a connection to a TeamTalkServer.
It is used to send and receive messages, join and leave channels, and perform other actions.
In addition, it's also here that events are dispatched.
"""

import asyncio
import os
import logging
import time
import ctypes
from typing import List, Union

from ._utils import _getAbsTimeDiff, _waitForEvent, _waitForCmd, _do_after
from .channel import Channel as TeamTalkChannel
from .channel import ChannelType
from .enums import TeamTalkServerInfo, UserStatusMode, UserType
from .exceptions import PermissionError
from .implementation.TeamTalkPy import TeamTalk5 as sdk
from .message import BroadcastMessage, ChannelMessage, CustomMessage, DirectMessage
from .permission import Permission
from .server import Server as TeamTalkServer
from .tt_file import RemoteFile
from .user import User as TeamTalkUser
from .user_account import UserAccount as TeamTalkUserAccount
from .user_account import BannedUserAccount as TeamTalkBannedUserAccount


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
        self.channel = lambda: self.get_channel(self.super.getMyChannelID())
        self.connected = False
        self.logged_in = False
        self.init_time = time.time()
        self.user_accounts = []
        self.banned_users = []

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

        If the user is an admin, they have all permissions.

        Args:
            permission: The permission to check for.

        Returns:
            bool: True if the bot has the permission, False otherwise.
        """
        user = self.super.getMyUserAccount()
        # first check if they are an admin
        if user.uUserType == sdk.UserType.USERTYPE_ADMIN:
            return True
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
        return TeamTalkChannel(self, channel_id)

    def get_path_from_channel(self, channel: Union[TeamTalkChannel, int]) -> str:
        """Gets the path of a channel.

        Args:
            channel: The channel to get the path of.

        Returns:
            str: The path of the channel.

        Raises:
            TypeError: If the channel is not of type teamtalk.Channel or int.
            ValueError: If the channel is not found.
        """
        if isinstance(channel, TeamTalkChannel):
            channel = channel.id
        # variable to hold the path
        path = sdk.TTCHAR()
        result = sdk._GetChannelPath(self.super, channel, path)
        if not result:
            raise ValueError("Channel not found")
        return path.value

    def get_channel_from_path(self, path: str) -> TeamTalkChannel:
        """Gets a channel by its path.

        Args:
            path: The path of the channel to get.

        Returns:
            TeamTalkChannel: The channel.

        Raises:
            ValueError: If the channel is not found.
        """
        result = sdk._GetChannelIDFromPath(self.super, sdk.ttstr(path))
        if result == 0:
            raise ValueError("Channel not found")
        return TeamTalkChannel(self, result)

    # create a channel. Take in a name, parent channel. Optionally take in a topic, password and channel type
    def create_channel(
        self,
        name: str,
        parent_channel: Union[TeamTalkChannel, int],
        topic: str = "",
        password: str = "",
        channel_type: ChannelType = ChannelType.CHANNEL_DEFAULT,
    ) -> bool:
        """Creates a channel.

        Args:
            name: The name of the channel to create.
            parent_channel: The parent channel of the channel.
            topic: The topic of the channel.
            password: The password of the channel. Leave empty for no password.
            channel_type: The type of the channel. Defaults to CHANNEL_DEFAULT.

        Raises:
            PermissionError: If the bot does not have permission to create channels.
            ValueError: If the channel could not be created.

        Returns:
            bool: True if the channel was created, False otherwise.
        """
        if not self.has_permission(Permission.MODIFY_CHANNELS):
            raise PermissionError("The bot does not have permission to create channels")
        if isinstance(parent_channel, TeamTalkChannel):
            parent_channel = parent_channel.id
        new_channel = sdk.Channel()
        new_channel.nParentID = parent_channel
        new_channel.szName = sdk.ttstr(name)
        new_channel.szTopic = sdk.ttstr(topic)
        new_channel.szPassword = sdk.ttstr(password)
        new_channel.bPassword = password != ""
        new_channel.uChannelType = channel_type
        result = sdk._DoMakeChannel(self._tt, new_channel)
        if result == -1:
            raise ValueError("Channel could not be created")
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to create channels")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_ALREADY_EXISTS:
                raise ValueError("Channel already exists")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                raise ValueError("Combined channel path is too long. Try using a shorter channel name")
            if err_nr == sdk.ClientError.CMDERR_INCORRECT_CHANNEL_PASSWORD:
                raise ValueError("Channel password too long")
        return True

    def delete_channel(self, channel: Union[TeamTalkChannel, int]):
        """Deletes a channel.

        Args:
            channel: The channel to delete.

        Raises:
            TypeError: If the channel is not of type teamtalk.Channel or int.
            PermissionError: If the bot doesn't have the permission to delete the channel.
            ValueError: If the channel is not found.

        Returns:
            bool: True if the channel was deleted.
        """
        if not self.has_permission(Permission.MODIFY_CHANNELS):
            raise PermissionError("The bot does not have permission to delete channels")
        if isinstance(channel, TeamTalkChannel):
            channel = channel.id
        result = sdk._DoRemoveChannel(self._tt, channel)
        if result == -1:
            raise ValueError("Channel could not be deleted")
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to delete channels")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                raise ValueError("Channel not found.")
        return True

    def make_channel_operator(
        self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkUser, int], operator_password: str = ""
    ) -> bool:
        """Makes a user the channel operator.

        Args:
            user: The user to make the channel operator.
            channel: The channel to make the user the channel operator in.
            operator_password: The operator password of the channel.

        Raises:
            TypeError: If the user or channel is not of type teamtalk.User or int.
            PermissionError: If the bot doesn't have the permission to make a user the channel operator.
            ValueError: If the user or channel is not found.

        Returns:
            bool: True if the user was made the channel operator, False otherwise.
        """
        if isinstance(user, int):
            user = self.get_user(user)
        if isinstance(channel, int):
            channel = self.get_channel(channel)
        result = sdk.DoChannelOpEx(self.super, user.id, channel.id, sdk.ttstr(operator_password), True)
        if result == -1:
            raise PermissionError("The bot does not have the permission to make a user the channel operator")
            return False
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to make a user the channel operator")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                raise ValueError("The channel does not exist")
            if err_nr == sdk.ClientError.CMDERR_USER_NOT_FOUND:
                raise ValueError("The user does not exist")
            if err_nr == sdk.ClientError.CMDERR_INCORRECT_OP_PASSWORD:
                raise ValueError("The operator password is incorrect")
            return False
        return True

    def remove_channel_operator(
        self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkUser, int], operator_password: str = ""
    ) -> bool:
        """Removes a user as the channel operator.

        Args:
            user: The user to make the channel operator.
            channel: The channel to make the user the channel operator in.
            operator_password: The operator password of the channel.

        Raises:
            TypeError: If the user or channel is not of type teamtalk.User or int.
            PermissionError: If the bot doesn't have the permission to make a user the channel operator.
            ValueError: If the channel or user does not exist.

        Returns:
            bool: True if the user was removed as the channel operator, False otherwise.
        """
        if isinstance(user, int):
            user = self.get_user(user)
        if isinstance(channel, int):
            channel = self.get_channel(channel)
        result = sdk.DoChannelOpEx(self.super, user.id, channel.id, sdk.ttstr(operator_password), False)
        if result == -1:
            raise PermissionError("The bot does not have the permission to make a user the channel operator")
            return False
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to make a user the channel operator")
            if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                raise ValueError("The channel does not exist")
            if err_nr == sdk.ClientError.CMDERR_USER_NOT_FOUND:
                raise ValueError("The user does not exist")
            if err_nr == sdk.ClientError.CMDERR_INCORRECT_OP_PASSWORD:
                raise ValueError("The operator password is incorrect")
            return False
        return True

    def get_user(self, user_id: int) -> TeamTalkUser:
        """Gets a user by its ID.

        Args:
            user_id: The ID of the user to get.

        Returns:
            TeamTalkUser: The user.
        """
        return TeamTalkUser(self, user_id)

    # user account stuff
    def create_user_account(self, username: str, password: str, usertype: UserType) -> TeamTalkUserAccount:  # noqa
        """Creates a user account on the server.

        Args:
            username: The username of the user account.
            password: The password of the user account.
            usertype: The type of the user account.

        Returns:
            TeamTalkUserAccount: The user account.

        Raises:
            ValueError: If the username or password is invalid.
            PermissionError: If the bot does not have permission to create a user account or if the bot is not logged in.
        """
        account = sdk.UserAccount()
        account.szUsername = username
        account.szPassword = password
        account.uUserType = usertype
        result = sdk._DoNewUserAccount(self._tt, account)
        if result == -1:
            raise ValueError("Username or password is invalid")
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_INVALID_USERNAME:
                raise ValueError("Username is invalid")
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to create a user account")
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
        return True

    def delete_user_account(self, username: str) -> bool:
        """Deletes a user account.

        Args:
            username: The username of the user account to delete.

        Returns:
            bool: True if the user account was deleted, False otherwise.

        Raises:
            ValueError: If the username is empty or the user account does not exist.
            PermissionError: If the user does not have permission to delete a user account.
        """
        if not username:
            raise ValueError("Username is empty")
        username = sdk.ttstr(username)
        result = sdk._DoDeleteUserAccount(self._tt, username)
        if result == -1:
            raise ValueError("User account does not exist")
        cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
        if not cmd_result:
            err_nr = cmd_err.nErrorNo
            if err_nr == sdk.ClientError.CMDERR_NOT_AUTHORIZED:
                raise PermissionError("The bot does not have permission to delete a user account")
            if err_nr == sdk.ClientError.CMDERR_NOT_LOGGEDIN:
                raise PermissionError("The bot is not logged in")
            if err_nr == sdk.ClientError.CMDERR_ACCOUNT_NOT_FOUND:
                raise ValueError("User account does not exist")
        return True

    async def list_user_accounts(self) -> List[TeamTalkUserAccount]:
        """Lists all user accounts on the server.

        Returns:
            A list of all user accounts.

        Raises:
            PermissionError: If the bot is not an admin.
            ValueError: If an unknown error occurred.
        """
        if not self.is_admin():
            raise PermissionError("The bot is not an admin")
        self.user_accounts = []
        result = sdk._DoListUserAccounts(self._tt, 0, 1000000)
        if result == -1:
            raise ValueError("Unknown error")
        await asyncio.sleep(1)
        return self.user_accounts

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
            ValueError: If the user or channel is not found.
        """
        # first check if we are kicking from channel or server
        if channel == 0:  # server
            if not self.has_permission(Permission.KICK_USERS):
                raise PermissionError("You do not have permission to kick users")
            _log.debug(f"Kicking user {user} from channel {channel}")
            self._do_cmd(user, channel, "_DoKickUser")
        else:  # channel
            if not self.has_permission(Permission.KICK_USERS_FROM_CHANNEL) or not sdk._IsChannelOperator(
                self._tt, self.super.getMyUserID(), channel
            ):
                raise PermissionError("You do not have permission to kick users from channels")
            result = self._do_cmd(user, channel, "_DoKickUser")
        if result == -1:
            raise ValueError("Uknown error")
            cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
            if not cmd_result:
                err_nr = cmd_err.nErrorNo
                if err_nr == sdk.ClientError.CMDERR_USER_NOT_FOUND:
                    raise ValueError("User not found")
                if err_nr == sdk.ClientError.CMDERR_CHANNEL_NOT_FOUND:
                    raise ValueError("Channel not found")
            return cmd_result

    def ban_user(self, user: Union[TeamTalkUser, int], channel: Union[TeamTalkChannel, int]) -> None:
        """Bans a user from a channel or the server.

        Args:
            user: The user to ban.
            channel: The channel to ban the user from. If 0, the user will be banned from the server. # noqa

        Raises:
            PermissionError: If the bot does not have permission to ban users.
            TypeError: If the user or channel is not a subclass of User or Channel.
            ValueError: If the user is not found.
        """
        if not self.has_permission(Permission.BAN_USERS):
            raise PermissionError("You do not have permission to ban users")
        _log.debug(f"Banning user {user} from channel {channel}")
        result = self._do_cmd(user, channel, "_DoBanUser")
        if result == -1:
            raise ValueError("Uknown error")
            cmd_result, cmd_err = _waitForCmd(self.super, result, 2000)
            if not cmd_result:
                err_nr = cmd_err.nErrorNo
                if err_nr == sdk.ClientError.CMDERR_USER_NOT_FOUND:
                    raise ValueError("User not found")
            return cmd_result

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

    async def list_banned_users(self) -> List[TeamTalkBannedUserAccount]:
        """Lists all banned users.

        Returns:
            List[BannedUserAccount]: A list of banned users.

        Raises:
            PermissionError: If the bot is not an admin.
            ValueError: If an unknown error occurs.
        """
        if not self.is_admin():
            raise PermissionError("The bot is not an admin")
        self.banned_users = []
        result = sdk._DoListBans(self._tt, 0, 0, 1000000)
        if result == -1:
            raise ValueError("Unknown error")
        await asyncio.sleep(1)
        return self.banned_users

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
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_USERACCOUNT:
            account = TeamTalkUserAccount(self, msg.useraccount)
            self.user_accounts.append(account)
            return
        if event == sdk.ClientEvent.CLIENTEVENT_CMD_BANNEDUSER:
            # cast our msg.useraccount to a banned user
            banned_user_struct = sdk.BannedUser()
            ctypes.memmove(ctypes.byref(banned_user_struct), ctypes.byref(msg.useraccount), ctypes.sizeof(sdk.BannedUser))
            banned_user = TeamTalkBannedUserAccount(self, banned_user_struct)
            self.banned_users.append(banned_user)
            return
        else:
            # if we haven't handled the event, log it
            # except if it's CLIENTEVENT_CMD_PROCESSING or CLIENTEVENT_CMD_ERROR or CLIENTEVENT_CMD_SUCCESS
            if event not in (
                sdk.ClientEvent.CLIENTEVENT_CMD_PROCESSING,
                sdk.ClientEvent.CLIENTEVENT_CMD_ERROR,
                sdk.ClientEvent.CLIENTEVENT_CMD_SUCCESS,
            ):
                _log.warning(f"Unhandled event: {event}")

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
        return sdk_func(self._tt, user_id, channel_id)
