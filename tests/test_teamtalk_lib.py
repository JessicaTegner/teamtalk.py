import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../",
        "teamtalk",
        "implementation",
        "TeamTalkPy",
    )
)
from TeamTalk5 import *


def test_ttypes():
    # Run DBG_SIZEOF() on all structs
    ac = AudioCodec()
    bu = BannedUser()
    vf = VideoFormat()
    oc = OpusCodec()
    c = Channel()
    cs = ClientStatistics()
    rf = RemoteFile()
    ft = FileTransfer()
    # mfs = MediaFileStatus
    sp = ServerProperties()
    ss = ServerStatistics()
    sd = SoundDevice()
    sc = SpeexCodec()
    tm = TextMessage()
    u = User()
    ua = UserAccount()
    us = UserStatistics()
    vcd = VideoCaptureDevice()
    vc = VideoCodec()
    acc = AudioConfig()
    spxvbr = SpeexVBRCodec()
    vf = VideoFrame()
    ab = AudioBlock()
    af = AudioFormat()
    mfi = MediaFileInfo()
    cem = ClientErrorMsg()
    di = DesktopInput()
    spxdsp = SpeexDSP()
    app = AudioPreprocessor()
    ttapp = TTAudioPreprocessor()
    mfp = MediaFilePlayback()
    ck = ClientKeepAlive()
    aip = AudioInputProgress()
    jit = JitterConfig()
    webrtc = WebRTCAudioPreprocessor()
    enc = EncryptionContext()
