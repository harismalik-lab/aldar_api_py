"""
This module contains class used for reCAPTCHA_V3 integration
"""
import requests

from common.api_utils import get_logger


class CaptchaV3(object):

    CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    CAPTCHA_SECRET_KEY = "6Ld-ProZAAAAAEiwgBHAp_6m1HwoPzhSb8qKk6PM"
    CAPTCHA_MINIMUM_SCORE = 0.4

    logger = get_logger('captcha_verification/captcha_verify.log', 'captcha_logger')

    def verify_captcha(self, response):
        """
        Verify google captcha authentication
        :param str response: response of captcha UI
        :rtype: bool
        """
        if response:
            try:
                headers = {
                    "Content-type": "application/x-www-form-urlencoded",
                    "User-agent": "reCAPTCHA Python"
                }
                data = {
                    'secret': self.CAPTCHA_SECRET_KEY,
                    'response': response
                }
                captcha_response = requests.post(self.CAPTCHA_VERIFY_URL, data=data, headers=headers)
                captcha_response = captcha_response.json()
                if captcha_response.get('success'):
                    if captcha_response.get('score') <= self.CAPTCHA_MINIMUM_SCORE:
                        return False
                    return True
            except Exception:
                self.logger.exception('Failed to verify captcha')
        return False


captcha_v3 = CaptchaV3()
