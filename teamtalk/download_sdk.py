"""Download the TeamTalk SDK and extract it to the implementation directory."""

from .tools import ttsdk_downloader


def download_sdk():
    """Download the TeamTalk SDK and extract it to the implementation directory."""
    ttsdk_downloader.install()
