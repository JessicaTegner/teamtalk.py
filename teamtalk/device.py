"""Provides the SoundDevice class representing a TeamTalk audio device."""

from .implementation.TeamTalkPy import TeamTalk5 as sdk

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
        """Gets the ID of the device.

        Returns:
            The integer device ID.
        """
        return self._device_struct.nDeviceID

    @property
    def name(self) -> str:
        """Gets the name of the device.

        Returns:
            The string name of the device.
        """
        return sdk.ttstr(self._device_struct.szDeviceName)

    @property
    def sound_system(self) -> int:
         """Gets the sound system ID (e.g., WASAPI, ALSA).

         Returns:
            The integer ID of the sound system.
         """
         return self._device_struct.nSoundSystem

    @property
    def is_input(self) -> bool:
        """Returns True if this is an input device.

        Returns:
            True if the device has input channels, False otherwise.
        """
        return self._device_struct.nMaxInputChannels > 0

    @property
    def is_output(self) -> bool:
        """Returns True if this is an output device.

        Returns:
            True if the device has output channels, False otherwise.
        """
        return self._device_struct.nMaxOutputChannels > 0

    def __repr__(self) -> str:
        """Returns a string representation of the device.

        Returns:
            A developer-friendly string representation.
        """
        input_output = []
        if self.is_input:
            input_output.append("Input")
        if self.is_output:
            input_output.append("Output")
        type_str = "/".join(input_output)
        return f"SoundDevice(id={self.id}, name='{self.name}', type='{type_str}')"