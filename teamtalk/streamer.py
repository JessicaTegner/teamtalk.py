"""A module containing the Streamer class.

This module contains the Streamer class, which is used to stream audio data to a TeamTalk channel.

.. warning::
   To use other files than .wav files, you need to have ffmpeg installed on your system.

.. warning::
   To stream urls, you need to have yt-dlp installed on your system.

Example:
    >>> import teamtalk
    >>> # asuming we have a bot in the variable bot
    >>> @bot.event
    >>> async def on_message(message):
    >>>     if message.content.lower() == "play":
    >>>         streamer = teamtalk.Streamer.get_streamer_for_channel(message.channel)
    >>>         streamer.stream("path/to/file.wav")
    >>> # or for an url
    >>> streamer.stream("https://www.example.com/youtube/or/other/stream")


It's also possible to stream audio from an arbitrary data stream, such as a microphone.
To do this, you need to set the correct sample rate and number of channels on initialization,
and then feed the data to the streamer as it becomes available.
The data needs to be in 16 bit PCM format (pcm_s16le).

Example:
    >>> import teamtalk
    >>> # asuming we have a bot in the variable bot
    >>> @bot.event
    >>> async def on_message(message):
    >>>     if message.content.lower() == "play":
    >>>         streamer = teamtalk.Streamer.get_streamer_for_channel(message.channel, sample_rate=48000, channels=2)
    >>>         # we could get the data from any source, so let's assume it's coming from a live microphone.
    >>>         data_stream = # connect to microphone
    >>>         while True:
    >>>             # get the data from the stream
    >>>             data = data_stream.read(streamer.block_size*16) # we are reading 16 chunks at a time to combat buffering
    >>>             if data == 0:
    >>>                 break
    >>>             # add the data to the streamer
    >>>             streamer.feed(data)
    >>>         # close the connection to our microphone
"""

import ctypes
import threading
import random
import subprocess
import multiprocessing

from .implementation.TeamTalkPy import TeamTalk5 as sdk

from .channel import Channel as TeamTalkChannel

_audio_streamers = {}


class Streamer:
    """A class representing a streamer for audio data to a TeamTalk channel."""

    @staticmethod
    def get_streamer_for_channel(
        channel: TeamTalkChannel, sample_rate: int = 48000, channels: int = 2, block_size: int = 4 * 1024
    ):
        """Gets a streamer for a channel.

        Args:
            channel (TeamTalkChannel): The TeamTalk channel to get the streamer for.
            sample_rate (int, optional): The sample rate of the audio data. Defaults to 48000.
            channels (int, optional): The number of channels in the audio data. Defaults to 2.
            block_size (int, optional): The block size of the audio data. Defaults to 4 * 1024 (4kb)

        Returns:
            Streamer: The streamer for the channel.
        """
        if channel not in _audio_streamers:
            _audio_streamers[channel] = Streamer(channel, sample_rate, channels, block_size)
        return _audio_streamers[channel]

    def __init__(self, channel: TeamTalkChannel, sample_rate: int = 48000, channels: int = 2, block_size: int = 4 * 1024):
        """Initializes a new instance of the TeamTalkStreamer class.

        Args:
            channel (TeamTalkChannel): The TeamTalk channel to which the streamer streams the audio data.
            sample_rate (int, optional): The sample rate of the audio data. Defaults to 48000.
            channels (int, optional): The number of channels in the audio data. Defaults to 2.
            block_size (int, optional): The block size of the audio data. Defaults to 4 * 1024 (4kb)
        """
        self.channel = channel
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        # the list of blocks that will be streamed
        self.blocks = []
        self.current_data = b""
        # streamer id
        self.stream_id = random.randint(6000, 6999)
        # capabilities for  ffmpeg and yt-dlp
        self.ffmpeg_available = self._has_ffmpeg()
        self.yt_dlp_available = self._has_yt_dlp()
        # start the stream function on another thread
        self.running = True
        self._streamer_thread = threading.Thread(target=self._do_stream, daemon=True)
        self._streamer_thread.start()
        self._current_streamer_thread = None
        self._current_streamer_running = False
        self._stream_lock = threading.Lock()  # To ensure mutual exclusion when starting/stopping streams.

    def __del__(self):
        """Shuts down the streamer by adding a null-block to the blocks list and waiting for the blocks list to be empty."""
        # add a block with 0 length to the blocks list to stop the streamer
        self.blocks.append(b"")
        # wait for the blocks list to be empty
        while len(self.blocks) > 0:
            pass
        # stop the streamer
        self.running = False

    def stream(self, path: str) -> None:
        """Streams a file or url to the channel.

        Args:
            path (str): The path to the file or url to stream.

        Raises:
            RuntimeError: If yt-dlp is not installed and the path is an url, or ffmpeg is not installed.
            KeyboardInterrupt: If the stream is interrupted by a keyboard interrupt.
        """
        with self._stream_lock:
            self._request_stop_stream()  # Gracefully request the current stream to stop.
            self._wait_for_cleanup()  # Wait for the cleanup to complete.
            self._start_new_stream(path)  # Start the new stream.

    def _request_stop_stream(self):
        if self._current_streamer_thread is not None:
            self._current_streamer_running = False

    def _wait_for_cleanup(self):
        if self._current_streamer_thread:
            self.blocks.clear()  # Clear the blocks list, ensuring the streamer stops.
            self.blocks.append(b"")

    def _start_new_stream(self, path):
        self._current_streamer_running = True
        self._current_streamer_thread = threading.Thread(target=self._stream, args=(path,), daemon=True)
        self._current_streamer_thread.start()

    def _stream(self, path: str) -> None:
        if not self.ffmpeg_available:
            raise RuntimeError("Could not convert file to wav. ffmpeg is not installed.")
        if path.startswith("http"):
            if not self.yt_dlp_available:
                raise RuntimeError("Could not download file. yt-dlp is not installed.")
            ffmpeg_process, yt_dlp_process = self._get_url_data(path)
        else:
            ffmpeg_command = [
                'ffmpeg',
                '-i',
                path,  # Input URL
                '-f',
                'wav',  # Output format
                '-acodec',
                'pcm_s16le',  # Audio codec
                '-ar',
                f"{str(self.sample_rate)}",  # Sample rate
                '-ac',
                str(self.channels),  # Number of audio channels
                '-threads',
                str(multiprocessing.cpu_count()),  # Number of threads
                '-hide_banner',
                '-loglevel',
                'error',  # Suppress output
                '-',  # Output to stdout
            ]
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)
        try:
            while self._current_streamer_running:
                block = ffmpeg_process.stdout.read(self.block_size)
                if len(block) == 0:
                    break
                self.feed(block)
        except KeyboardInterrupt:
            raise
        finally:
            self._graceful_shutdown(ffmpeg_process)
            if path.startswith("http"):
                self._graceful_shutdown(yt_dlp_process)

    def _get_url_data(self, url):
        yt_dlp_command = [
            'yt-dlp',
            '-f',
            'bestaudio',
            '--extract-audio',
            '--audio-format',
            'best',
            '--audio-quality',
            '0',
            '--quiet',
            '-o',
            '-',
            url,
        ]
        ffmpeg_command = [
            'ffmpeg',
            '-i',
            'pipe:0',
            '-f',
            'wav',
            '-acodec',
            'pcm_s16le',
            '-ar',
            str(self.sample_rate),
            '-ac',
            str(self.channels),
            '-threads',
            str(multiprocessing.cpu_count()),
            '-hide_banner',
            '-loglevel',
            'error',
            '-',
        ]

        yt_dlp_process = subprocess.Popen(yt_dlp_command, stdout=subprocess.PIPE)
        return subprocess.Popen(ffmpeg_command, stdin=yt_dlp_process.stdout, stdout=subprocess.PIPE), yt_dlp_process

    def _graceful_shutdown(self, process):
        if process:
            process.terminate()  # Send SIGTERM
            try:
                process.wait(timeout=2)  # Wait for up to 5 seconds for the process to exit
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate in time
            finally:
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

    def feed(self, data: bytes) -> int:
        """Feeds data to the streamer.

        Args:
            data (bytes): The data to feed to the streamer.

        Returns:
            int: The stream id of the stream.
        """
        # first add the data to the current data
        self.current_data += data
        if len(self.current_data) >= self.block_size:
            # if it is, then split it into 4*1024 byte chunks
            chunks = [self.current_data[i : i + self.block_size] for i in range(0, len(self.current_data), self.block_size)]
            # then add all but the last chunk to the blocks list
            self.blocks.extend(chunks[:-1])
            # then set the current data to the last chunk
            self.current_data = chunks[-1]
        else:
            # if it is not, then just add the block to the blocks list
            self.blocks.append(data)
        return self.stream_id

    def _do_stream(self):
        while self.running:
            # if there are blocks to stream
            if len(self.blocks) > 0:
                # get the first block
                block = self.blocks[0]
                # create a new audio block
                audio_block = sdk.AudioBlock()
                audio_block.nStreamID = self.stream_id
                audio_block.nSampleRate = self.sample_rate
                audio_block.nChannels = self.channels
                audio_block.nSamples = len(block) // 4
                audio_block.lpRawAudio = ctypes.cast((ctypes.c_char * len(block)).from_buffer_copy(block), ctypes.c_void_p)
                audio_block.uStreamTypes = sdk.StreamType.STREAMTYPE_VOICE
                # send the audio block
                result = 0
                while result == 0:
                    result = sdk._InsertAudioBlock(self.channel.teamtalk._tt, audio_block)
                # remove the block from the blocks list
                self.blocks = self.blocks[1:]

    def _has_ffmpeg(self):
        # check if ffmpeg is installed
        try:
            result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                return False
        except FileNotFoundError:
            return False
        return True

    def _has_yt_dlp(self):
        # check if yt-dlp is installed
        try:
            result = subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                return False
        except FileNotFoundError:
            return False
        return True
