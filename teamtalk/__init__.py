# if the implementation can't be found. Try to download it
# from the internet and install it.

# first add our to be implmentation/TeamTalk_DLL to the path
import os
import sys

from ctypes import *

# if we are on linux we do a little hack for the LD_LIBRARY_PATH
try:
    if sys.platform.startswith("linux"):
        # get the full path to the implementation/TeamTalk_DLL folder
        libpath = os.path.join(os.path.dirname(__file__), "implementation", "TeamTalk_DLL", "libTeamTalk5.so")
        dll = cdll.LoadLibrary(libpath)
    from .implementation.TeamTalkPy import TeamTalk5 as sdk
except:
    from .download_sdk import download_sdk

    download_sdk()
    if sys.platform.startswith("linux"):
        # get the full path to the implementation/TeamTalk_DLL folder
        libpath = os.path.join(os.path.dirname(__file__), "implementation", "TeamTalk_DLL", "libTeamTalk5.so")
        dll = cdll.LoadLibrary(libpath)
    from .implementation.TeamTalkPy import TeamTalk5 as sdk

from .bot import TeamTalkBot
from .channel import Channel
from .enums import TeamTalkServerInfo, UserStatusMode, UserType
from .instance import TeamTalkInstance
from .message import BroadcastMessage, ChannelMessage, CustomMessage, DirectMessage
from .permission import Permission
from .streamer import Streamer
from .subscription import Subscription
