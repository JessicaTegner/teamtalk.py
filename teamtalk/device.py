from .implementation.TeamTalkPy import TeamTalk5 as sdk
from typing import List

class SoundDevice:
    """Represents a sound device available in TeamTalk."""

    def __init__(self, device_struct: sdk.SoundDevice):
        """Initializes a SoundDevice object.

        Args:
            device_struct: The sdk.SoundDevice struct from the TeamTalk SDK.
        """
        self._device_struct = device_struct

    @property
    def id(self) -> int:
        """Gets the ID of the device."""
        return self._device_struct.nDeviceID

    @property
    def name(self) -> str:
        """Gets the name of the device."""
        return sdk.ttstr(self._device_struct.szDeviceName)

    @property
    def sound_system(self) -> int:
         """Gets the sound system ID (e.g., WASAPI, ALSA)."""
         return self._device_struct.nSoundSystem

    @property
    def is_input(self) -> bool:
        """Returns True if this is an input device (microphone)."""
        return self._device_struct.nMaxInputChannels > 0

    @property
    def is_output(self) -> bool:
        """Returns True if this is an output device (speakers)."""
        return self._device_struct.nMaxOutputChannels > 0

    def __repr__(self) -> str:
        """Returns a string representation of the device."""
        input_output = []
        if self.is_input:
            input_output.append("Input")
        if self.is_output:
            input_output.append("Output")
        type_str = "/".join(input_output)
        return f"SoundDevice(id={self.id}, name='{self.name}', type='{type_str}')"