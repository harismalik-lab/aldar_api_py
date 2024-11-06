"""
Common api util methods reside here
"""
import base64
import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from Crypto.Cipher import AES
from flask import current_app, g

from common.constants import (
    MEMBERSHIP_CODE_DEFAULT_CARD_NUMBER,
    MEMBERSHIP_CODE_DEFAULT_LOCATION,
    MEMBERSHIP_CODE_PREFIX,
    OTP_RATE_LIMIT_SECONDS
)
from models.aldar_app.otp_history import OtpHistory
from models.aldar_app.rule import Rule
from models.entertainer_web.api_configuration import ApiConfiguration

cache = g.cache


def get_logger(filename='', name=''):
    """
    Return a logger with the specified name, creating it if necessary. If apm error logging is on then it also
    sends log to apm server otherwise it logs them in file.
    :param filename: log file name
    :param name: logger name
    :return:
    """
    parent_directory = os.path.dirname(filename)
    parent_directory = os.path.join(current_app.config.get('LOGS_PATH'), parent_directory)
    # create api log folders if not exist example outlet_api, country_api
    if parent_directory and not os.path.exists(parent_directory):
        os.makedirs(parent_directory)
    log_file_name = os.path.join(current_app.config.get('LOGS_PATH'), filename)
    logging_level = logging.INFO
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    # if apm error logging is on then initialize flask elastic apm logging
    logger = logging.getLogger(name)  # or pass string to give it a name
    # set TimedRotatingFileHandler for root, use very short interval for this example, typical
    # 'when' would be 'midnight' and no explicit interval
    handler = TimedRotatingFileHandler(log_file_name, when='midnight', backupCount=10)
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging_level)
    return logger


def get_iso_formatted_date(date_obj):
    """
    convert datetime object to iso formatted date str
    :param date_obj: datetime object
    :return: str
    """
    return "{}+04:00".format(date_obj.isoformat())


def pkcs7_padding(b_string, k=16):
    """
    Pad an input byte string according to PKCS#7
    """
    length = len(b_string)
    val = k - (length % k)
    return b_string + bytearray([val] * val)


def decode_params(key, salt, mode, encoded_params, add_padding=True):
    """
    Decodes params
    :param str mode: Decryption mode
    :param str key: Decryption key
    :param str salt: 16 bit salt
    :param byte encoded_params: Encoded params
    :rtype: dict
    """
    aes = AES.new(key, mode=mode, IV=salt)
    if add_padding:
        decrypted_str = aes.decrypt(pkcs7_padding(encoded_params, 16))
        decrypted_str = decrypted_str.decode(errors='ignore')
        if '}' in decrypted_str:
            found = decrypted_str.rfind('\n}') + 2
            if found < 2:
                found = decrypted_str.rfind('"}') + 2
            decrypted_str = decrypted_str[:found]
        else:
            found = decrypted_str.find('\n')
            if found > 0:
                decrypted_str = decrypted_str[0:found]
    else:
        decrypted_str = aes.decrypt(encoded_params)
        decrypted_str = decrypted_str.decode(errors='ignore')
        # '}' is expected to be the last CHAR after padding
        decrypted_str = decrypted_str[:decrypted_str.rfind("}") + 1]
    return decrypted_str


def encode_params(key, salt, mode, encoded_params):
    """
    Decodes params
    :param str mode: Decryption mode
    :param str key: Decryption key
    :param str salt: 16 bit salt
    :param byte encoded_params: Encoded params
    :rtype: dict
    """
    try:
        encoded_params = pkcs7_padding(encoded_params, 16)
        aes = AES.new(key, mode=mode, IV=salt)
        decrypted_str = aes.encrypt(encoded_params)
        return base64.b64encode(decrypted_str)
    except Exception:
        return ""


@cache.memoize(timeout=1800)
def get_company_rules_dict(company='ADR', env='DEV'):
    rules = Rule.get_all_active_by_company_and_env(company, env)
    rules_dict = {}
    for rule in rules:
        if rule.rule_value == 'true':
            rules_dict[rule.rule_key] = True
        elif rule.rule_value == 'false':
            rules_dict[rule.rule_key] = False
        elif rule.rule_value.isdigit():
            rules_dict[rule.rule_key] = int(rule.rule_value)
        else:
            rules_dict[rule.rule_key] = rule.rule_value
    return rules_dict


def remove_handlers(logger):
    """
    remove logger handlers
    :param logger:
    """
    for handler in getattr(logger, 'handlers', []):
        if not current_app.config.get('GENERATE_APM_ERROR_LOGS', False):
            handler.stream.close()
        logger.removeHandler(handler)


def rate_limit_otp(msisdn):
    """
    Rate limit OTP sending
    """
    valid_otp_send_datetime = datetime.datetime.now() - datetime.timedelta(seconds=OTP_RATE_LIMIT_SECONDS)
    otp_history = OtpHistory.get_latest_otp_history(msisdn)
    if otp_history and otp_history.created_at > valid_otp_send_datetime:
        return True
    return False


def generate_member_code(country, user_id):
    """
    Generates Membership code
    :param str country:  Country
    :param int user_id:  User id
    :rtype str
    """
    year = datetime.datetime.now().year
    location_code = country
    if not location_code:
        location_code = MEMBERSHIP_CODE_DEFAULT_LOCATION
    user_id = str(user_id)
    user_id = user_id.rjust(8, '0')
    membership_code = "{membership_code}{year}{location_code}{user_id}{card_number}".format(
        membership_code=MEMBERSHIP_CODE_PREFIX,
        year=year,
        location_code=location_code,
        user_id=user_id,
        card_number=MEMBERSHIP_CODE_DEFAULT_CARD_NUMBER
    )
    return membership_code


@cache.memoize(timeout=1800)
def get_api_configurations(company, environment, config_group=None):
    """
    get api configurations and set its key value
    :param str config_group: Config Group
    :param str company: Company
    :param str environment: App Env
    :return: configurations
    :rtype: dict
    """
    # getting api_configurations
    configs = {}
    api_configs = ApiConfiguration.get_configuration_by_company(company, environment, config_group)
    if api_configs:
        # creating a new dict by setting config_key as dict key and
        # config_value as value for its corresponding key
        for config in api_configs:
            if config.config_value == 'true':
                configs[config.config_key] = True
            elif config.config_value == 'false':
                configs[config.config_key] = False
            else:
                configs[config.config_key] = config.config_value
    return configs


def get_diff_in_hours_minutes_seconds(time_diff, d_translation, h_translation, m_translation, s_translation):
    """
    Gets a datetime timedelta object and returns a string containing difference in time in days, hours, minutes and
    seconds.

    :param timedelta time_diff: difference of two datetime objects
    :param str d_translation: Translation of days according to user language
    :param str m_translation: Translation of minutes according to user language
    :param str h_translation: Translation of hours according to user language
    :param str s_translation: Translation of seconds according to user language
    :return: difference of two dates in string form
    :rtype str
    """
    minute = 0
    hour = 0
    diff = ''
    minutes, seconds = divmod(time_diff.seconds, 60)
    if minutes > 60:
        hour, minute = divmod(minutes, 60)
    if time_diff.days:
        diff += '{} {} '.format(time_diff.days, d_translation)
    if hour:
        diff += '{} {} '.format(hour, h_translation)
    if minute:
        diff += '{} {} '.format(minute, m_translation)
    if seconds:
        diff += '{} {}'.format(seconds, s_translation)
    return diff.strip()
