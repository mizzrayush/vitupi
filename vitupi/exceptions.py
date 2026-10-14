"""
Custom exceptions for the Vitupi library.
"""


class VitupiError(Exception):
    """Base exception for all Vitupi errors."""
    pass


class VideoDecodingError(VitupiError):
    """Raised when a video file cannot be opened, decoded, or read."""
    pass


class VideoMetadataError(VitupiError):
    """Raised when video metadata cannot be parsed or is invalid."""
    pass


class SceneDetectionError(VitupiError):
    """Raised when scene detection fails during execution."""
    pass


class ConfigurationError(VitupiError):
    """Raised when an invalid configuration or mode is provided."""
    pass


class ExtractionError(VitupiError):
    """Raised when photograph extraction fails."""
    pass
