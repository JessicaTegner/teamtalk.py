"""TeamTalk enums and constants."""

from typing_extensions import Self


class TeamTalkServerInfo:
    """Holds the required information to connect and login to a TeamTalk server."""

    def __init__(
        self,
        host: str,
        tcp_port: int,
        udp_port: int,
        username: str,
        password: str = "",
        encrypted: bool = False,
        nickname: str = "",
        join_channel_id: int = -1,
        join_channel_password: str = "",
    ) -> None:
        """Initialize a TeamTalkServerInfo object.

        Args:
            host (str): The host of the TeamTalk server.
            tcp_port (int): The TCP port of the TeamTalk server.
            udp_port (int): The UDP port of the TeamTalk server.
            username (str): The username to login with.
            password (str): The password to login with. Defaults to "" (no password).
            encrypted (bool): Whether or not to use encryption. Defaults to False.
            nickname (str): The nickname to use. Defaults to "teamtalk.py Bot".
            join_channel_id (int): The channel ID to join. Defaults to -1 (don't join a channel on login). Set to 0 to join the root channel, or a positive integer to join a specific channel. # noqa: E501
            join_channel_password (str): The password to join the channel with. Defaults to "" (no password).
        """
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.username = username
        self.password = password
        self.encrypted = encrypted
        self.nickname = nickname if nickname else username
        self.join_channel_id = join_channel_id
        self.join_channel_password = join_channel_password

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Construct a TeamTalkServerInfo object from a dictionary.

        Args:
            data (dict): The dictionary to construct the object from.

        Returns:
            Self: The constructed object.
        """
        return cls(**data)

    # convert this object to a dictionary
    def to_dict(self) -> dict:
        """Convert this object to a dictionary.

        Returns:
            dict: The dictionary representation of this object.
        """
        return {
            "host": self.host,
            "tcp_port": self.tcp_port,
            "udp_port": self.udp_port,
            "username": self.username,
            "password": self.password,
            "encrypted": self.encrypted,
            "nickname": self.nickname if self.nickname else "",
            "join_channel_id": self.join_channel_id,
            "join_channel_password": self.join_channel_password,
        }

    # compare this object to another object
    def __eq__(self, other: object) -> bool:
        """Compare this object to another object.

        Args:
            other: The object to compare to.

        Returns:
            bool: Whether or not the objects are equal.
        """
        if not isinstance(other, TeamTalkServerInfo):
            return False
        return (
            self.host == other.host
            and self.tcp_port == other.tcp_port
            and self.udp_port == other.udp_port
            and self.username == other.username
            and self.password == other.password
            and self.encrypted == other.encrypted
        )

    # compare this object to another object
    def __ne__(self, other: object) -> bool:
        """Compare this object to another object.

        Args:
            other: The object to compare to.

        Returns:
            bool: Whether or not the objects are not equal.
        """
        return not self.__eq__(other)


class UserStatusMode:
    """The status mode of a user. This is used in the teamtalk.TeamTalkInstance.change_status call."""

    ONLINE = 0
    AWAY = 1
    QUESTION = 2


class UserType:
    """The type of a user account."""

    DEFAULT = 0x1
    ADMIN = 0x02
