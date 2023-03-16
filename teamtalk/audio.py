"""This module contains the AudioBlock class.

Not to be confused with the underlying AudioBlock class, this is used in the "on_user_audio" event. # noqa

        Example
        ---------

        .. code-block:: python3

            @client.event
            async def on_user_audio(block):
                print(block.user) # the teamtalk.User that the audio is from
                print(block.data) # the audio data
                # for more information, see the AudioBlock class


        See the :doc:`event Reference </events>` for more information and a list of all events.


"""

from .implementation.TeamTalkPy import TeamTalk5 as sdk

from ._utils import _get_tt_obj_attribute


_AcquireUserAudioBlock = sdk.function_factory(
    sdk.dll.TT_AcquireUserAudioBlock, [sdk.AudioBlock, [sdk._TTInstance, sdk.INT32, sdk.INT32]]
)
_ReleaseUserAudioBlock = sdk.function_factory(
    sdk.dll.TT_ReleaseUserAudioBlock, [sdk.BOOL, [sdk._TTInstance, sdk.POINTER(sdk.AudioBlock)]]
)


class AudioBlock:
    """Represents an audio block for the on_user_audio event.

    Attributes:
        user: The user that the audio is from.
        id: The stream ID of the audio block.
        data: The audio data.
        sample_rate: The sample rate of the audio data.
        channels: The number of channels in the audio data.
        samples: The number of samples in the audio data.
    """

    def __init__(self, user, block):
        """Represents an audio block for the on_user_audio event.

        Args:
            user: The user that the audio is from.
            block: The underlying AudioBlock object.
        """
        self.user = user
        self._block = block
        self.id = block.nStreamID
        self.data = block.lpRawAudio

    def __getattr__(self, name: str):
        """Try to get the attribute from the AUdioBlock object.

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
            return _get_tt_obj_attribute(self._block, name)
