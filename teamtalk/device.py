"""Provides the SoundDevice class representing a TeamTalk audio device."""

from .implementation.TeamTalkPy import TeamTalk5 as sdk
from ._utils import _get_tt_obj_attribute


class SoundDevice:
    """Represents a sound device available in TeamTalk."""

    def __init__(self, device_struct: sdk.SoundDevice, is_default_input: bool = False):
        """Initializes a SoundDevice object.

        Args:
            device_struct: The sdk.SoundDevice struct from the TeamTalk SDK.
            is_default_input: True if this is the default system input device.
        """
        self._device_struct = device_struct
        self._is_default_input = is_default_input

    def __getattr__(self, name: str):  # noqa: DAR101, DAR401
        """Gets an attribute from the underlying SDK structure.

        Args:
            name: The pythonic name of the attribute to get.

        Returns:
            The value of the attribute from the SDK structure.

        Raises:
            AttributeError: If the attribute is not found in the structure.
        """
        if name == "_device_struct":
            return self.__dict__["_device_struct"]
        if name == "_is_default_input":
            return self.__dict__["_is_default_input"]
        try:
            value = _get_tt_obj_attribute(self._device_struct, name)
            if isinstance(value, (bytes, sdk.TTCHAR, sdk.TTCHAR_P)):
                return sdk.ttstr(value)
            return value
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property  # noqa: DAR201
    def id(self) -> int:
        """Gets the ID of the device.

        Returns:
            The integer device ID.
        """
        return self.device_id

    @property  # noqa: DAR201
    def name(self) -> str:
        """Gets the name of the device.

        Returns:
            The string name of the device.
        """
        return self.device_name

    @property  # noqa: DAR201
    def sound_system(self) -> int:
        """Gets the sound system ID (e.g., WASAPI, ALSA).

        Returns:
            The integer ID of the sound system.
        """
        return self.sound_system

    @property  # noqa: DAR201
    def is_input(self) -> bool:
        """Returns True if this is an input device.

        Returns:
            True if the device has input channels, False otherwise.
        """
        try:
            return self.max_input_channels > 0
        except AttributeError:
            return False

    @property  # noqa: DAR201
    def is_output(self) -> bool:
        """Returns True if this is an output device.

        Returns:
            True if the device has output channels, False otherwise.
        """
        try:
            return self.max_output_channels > 0
        except AttributeError:
            return False

    @property  # noqa: DAR201
    def is_default_input(self) -> bool:
        """Returns True if this is the default system input device.

        Returns:
            True if the device was marked as the default input, False otherwise.
        """
        return self._is_default_input

    def __repr__(self) -> str:  # noqa: DAR201
        """Return a developer-friendly string representation of the device.

        Returns:
            A string representation of the SoundDevice instance.
        """
        input_output = []
        default_marker = " (Default)" if self.is_default_input else ""
        try:
            if self.is_input:
                input_output.append("Input")
            if self.is_output:
                input_output.append("Output")
        except AttributeError:
            pass
        type_str = "/".join(input_output)
        try:
            return f"SoundDevice(id={self.id}, name='{self.name}{default_marker}', type='{type_str}')"
        except AttributeError:
            _id = getattr(self._device_struct, 'nDeviceID', 'N/A')
            _name = sdk.ttstr(getattr(self._device_struct, 'szDeviceName', 'N/A'))
            return f"SoundDevice(id={_id}, name='{_name}{default_marker}', type='{type_str}')"
