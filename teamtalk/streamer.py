"""A module containing the Streamer class.

This module contains the Streamer class, which is used to stream audio data to a TeamTalk channel.

.. warning::
   To use other files than .wav files, you need to have ffmpeg installed on your system.

Example:
    >>> import teamtalk
    >>> # asuming we have a bot in the variable bot
    >>> @bot.event
    >>> async def on_message(message):
    >>>     if message.content.lower() == "play":
    >>>         stream = teamtalk.Streamer(message.channel)
    >>>         stream.stream_file("test.wav")


It's also possible to stream audio from an arbitrary data stream, such as a microphone or a url stream.
To do this, you need to set the correct sample rate and number of channels on initialization,
and then feed the data to the streamer as it becomes available.
The data needs to be in 16 bit PCM format (pcm_s16le).

Example:
    >>> import teamtalk
    >>> # asuming we have a bot in the variable bot
    >>> @bot.event
    >>> async def on_message(message):
    >>>     if message.content.lower() == "play":
    >>>         stream = teamtalk.Stream(message.channel, sample_rate=48000, channels=2)
    >>>         # we could get the data from any source, so let's assume it's coming from a live microphone and/or url stream
    >>>         data_stream = # connect to microphone and/or url stream
    >>>         while True:
    >>>             # get the data from the stream
    >>>             data = data_stream.read(streamer.block_size*16) # we are reading 16 chunks at a time to combat buffering
    >>>             if data == 0:
    >>>                 break
    >>>             # add the data to the streamer
    >>>             stream.feed(data)
    >>>         # close the connection to our microphone and/or url stream
"""

import os
import ctypes
import threading
import random
import subprocess
import tempfile

import PyWave

from .implementation.TeamTalkPy import TeamTalk5 as sdk

from .channel import Channel as TeamTalkChannel


class Streamer:
    """A class representing a streamer for audio data to a TeamTalk channel."""

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
        # start the stream function on another thread
        self.running = True
        threading.Thread(target=self._do_stream).start()

    def __del__(self):
        """Shuts down the streamer by adding a null-block to the blocks list and waiting for the blocks list to be empty."""
        # add a block with 0 length to the blocks list to stop the streamer
        self.blocks.append(b"")
        # wait for the blocks list to be empty
        while len(self.blocks) > 0:
            pass
        # stop the streamer
        self.running = False

    def stream_file(self, filepath: str, _tried: int = 0) -> int:
        """Streams a file to the channel.

        Args:
            filepath (str): The path to the file to stream.

        Returns:
            int: The stream id of the stream.

        Raises:
            FileNotFoundError: If the file could not be found.
            RuntimeError: If the file could not be opened as a wav file or if the file could not be converted to a wav file.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Could not find file {filepath}")
        try:
            wf = PyWave.open(filepath, "r")
        except PyWave.PyWaveError:
            if _tried < 3:
                new_filepath = self._convert_to_wav(filepath)
                return self.stream_file(new_filepath, _tried=_tried + 1)
            else:
                raise RuntimeError(f"Could not open file {filepath}.")
            # not normally done, but since we have a file, we don't need to asume
        self.sample_rate = wf.frequency
        self.channels = wf.channels
        while True:
            block = wf.read(self.block_size * 16)
            if len(block) == 0:
                break
            self.feed(block)
        wf.close()
        return self.stream_id

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

    def _convert_to_wav(self, filepath):
        if not self._has_ffmpeg():
            raise RuntimeError("Could not convert file to wav. ffmpeg is not installed.")
        # get a path to a temp dir we can write to
        temp_dir = tempfile.gettempdir()
        # make sure it exists
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)
        # get a path to a randomly named temp file
        temp_file = os.path.join(temp_dir, next(tempfile._get_candidate_names()))
        # add a wav extension to the temp file
        temp_file = f"{temp_file}.wav"
        cmd = ["ffmpeg", "-i", filepath, "-acodec", "pcm_s16le", temp_file]
        # call our command, prinitng stdout and stderr if we fail
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Could not convert file {filepath} to wav.")
        return temp_file

    def _has_ffmpeg(self):
        # check if ffmpeg is installed
        try:
            result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                return False
        except FileNotFoundError:
            return False
        return True
