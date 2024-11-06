"""
Custom Exceptions
"""


class InvalidConfigResource(Exception):
    """
    Raises when BaseResource configs are missing or invalid.
    """
    pass


class LMSStatusZeroException(Exception):
    """
    Raises when LMS api return status 0
    """
    pass
