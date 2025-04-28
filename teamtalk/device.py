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

    def __getattr__(self, name: str):
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

    @property
    def is_default_input(self) -> bool:
        """Returns True if this is the default system input device.

        Returns:
            True if the device was marked as the default input, False otherwise.
        """
        return self._is_default_input

    def __repr__(self) -> str:
        """Return a developer-friendly string representation of the device.

        Returns:
            A string representation of the SoundDevice instance.
        """
        input_output = []
        default_marker = " (Default)" if self.is_default_input else ""
        try:
            if _get_tt_obj_attribute(self._device_struct, 'max_input_channels') > 0:
                input_output.append("Input")
            if _get_tt_obj_attribute(self._device_struct, 'max_output_channels') > 0:
                input_output.append("Output")
        except AttributeError:
            pass
        type_str = "/".join(input_output)
        try:
            _id = self.id
            _name = self.name
            return f"SoundDevice(id={_id}, name='{_name}{default_marker}', type='{type_str}')"
        except AttributeError:
            _id_fallback = getattr(self._device_struct, 'nDeviceID', 'N/A')
            _name_fallback = sdk.ttstr(getattr(self._device_struct, 'szDeviceName', 'N/A'))
            return f"SoundDevice(id={_id_fallback}, name='{_name_fallback}{default_marker}', type='{type_str}')"
