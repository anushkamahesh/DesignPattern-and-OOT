class ConfigurationError(ValueError):
    """Raised when a location configuration fails validation before persistence."""


class LocationNotFoundError(LookupError):
    """The requested location does not exist."""


class ZoneNotFoundError(LookupError):
    """The requested zone does not exist in that location."""


class DeviceNotFoundError(LookupError):
    """The requested device does not exist."""