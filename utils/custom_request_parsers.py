"""
Custom Request Field Parsers
"""
import datetime

from validate_email import validate_email

from common.constants import DEFAULT_DATE_FORMAT, SUPPORTED_LOCALES, VALID_CURRENCIES, DEFAULT_DATETIME_FORMAT, \
    TRANSACTION_TYPE_ACCRUAL, TRANSACTION_TYPE_REDEMPTION


def language(value):
    """
    Validates that provided language is among supported locales
    :param str value: Locale
    :rtype: str
    """
    if isinstance(value, str):
        if not value or value.lower() in SUPPORTED_LOCALES:
            return value.lower()
        raise ValueError('Invalid language "{}"'.format(value))


def business_category_retail(value):
    """
    Validates that provided business category is retail
    :param str value: Business Category
    :rtype: str
    """
    if isinstance(value, str):
        if value == 'retail':
            return value
        raise ValueError('Invalid business_category "{}"'.format(value))


def currency(value):
    """
    Validates that provided currency is among supported currencies
    :param str value: Currency
    :rtype: str
    """
    if isinstance(value, str):
        if not value or value.upper() in VALID_CURRENCIES:
            return value
        raise ValueError('Invalid currency "{}"'.format(value))


def boolean(value):
    """Parse the string ``"true"`` or ``"false"`` as a boolean (case
    insensitive). Also accepts ``"1"`` and ``"0"`` as ``True``/``False``
    (respectively). If the input is from the request JSON body, the type is
    already a native python boolean, and will be passed through without
    further parsing.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        raise ValueError("boolean type must be not-null")
    value = str(value).lower()
    if value in ('true', '1', 1, 'True'):
        return True
    if value in ('false', '0', 0, '', 'False'):
        return False
    raise ValueError("Invalid literal for boolean(): {0}".format(value))


def validate_gender(gender):
    """
    Validates that user is male or female
    """
    if isinstance(gender, str):
        gender = gender.lower()
        if gender in ('', 'male', 'female'):
            return gender
        raise ValueError('{} is not a valid gender'.format(gender))
    raise ValueError('"{}" is not of type string'.format(gender))


def device_list_for_sign_up(device_os):
    """
    Checks that the device os is android or ios or blackberry or wp
    """
    if isinstance(device_os, str):
        device_os_lower = device_os.lower()
        if device_os_lower in ['ios', 'android', 'web', ""]:
            return device_os_lower
        raise ValueError('{} is not a valid device os'.format(device_os))
    raise ValueError('Invalid __platform type, expected string got {}'.format(type(device_os)))


def date_validator(_date):
    """
    Formats date
    :param str _date: Datetime str
    """
    try:
        return datetime.datetime.strptime(_date, DEFAULT_DATE_FORMAT)
    except:
        raise ValueError('"{}" is invalid date'.format(_date))


def datetime_validator(_date):
    """
    Formats date
    :param str _date: Datetime str
    """
    try:
        return datetime.datetime.strptime(_date, DEFAULT_DATETIME_FORMAT)
    except:
        raise ValueError('"{}" is invalid datetime'.format(_date))


def check_positive(value):
    ivalue = float(value)
    if ivalue <= 0.0:
        raise ValueError("{} is an invalid positive value".format(value))
    return ivalue


def transaction_type(value):
    if value and value.lower() in (TRANSACTION_TYPE_ACCRUAL, TRANSACTION_TYPE_REDEMPTION):
        return value.lower()
    raise ValueError("{} is an invalid type expected 'Accrual' or 'Redemption'".format(value))


def validate_platform(platform):
    """
    Validates that __platform is valid
    """
    if isinstance(platform, str):
        platform = platform.lower()
        if platform in ('ios', 'android', 'web'):
            return platform
        raise ValueError('{} is not a valid platform'.format(platform))
    raise ValueError('{} is not a of type string'.format(platform))


def email(_email):
    """
    Validates provided email
    :param str _email: Email to be validated
    :rtype: str
    """
    if validate_email(_email):
        return _email
    else:
        raise ValueError('Invalid Email "{}"'.format(_email))


def resolution_status(_status):
    """
    Validates provided email
    :param _status:
    :rtype: str
    """
    if _status in (1, 2):
        return _status
    else:
        raise ValueError('Invalid resolution status "{}"'.format(_status))
