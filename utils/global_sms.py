"""
This module is dev Integration for `GlobalSMS Messaging Platform – Wisoft Solutions` to send sms for OTP
"""
import json

from flask import request
from requests.auth import HTTPBasicAuth

from common.api_utils import get_logger
from models.aldar_app.api_error_logs import ApiErrorLog
from utils.communicator import communicator


class GlobalSms(object):

    logger = get_logger('global_sms/global_sms.log', 'global_sms_logger')

    USER_NAME = 'aldarAPI'
    PASSWORD = 'hwnyaQJf'
    SOURCE = 'ALDAR'
    SEND_SMS_URL = 'https://globalsms.wisoftsolutions.com:1111/API/SendBulkSMS'
    REQUEST_METHOD = 'POST'

    def log_in_db(self, endpoint, method, request_body, request_header, response_body, http_error_code):
        """
        Global SMS error in db
        """
        try:
            log = ApiErrorLog(
                endpoint=endpoint,
                method=method,
                request_body=json.dumps(request_body),
                request_header=json.dumps(request_header),
                response_body=json.dumps(response_body),
                http_error_code=http_error_code,
                company='GLOBAL-SMS',
                error_message="",
                consumer_ip=request.remote_addr
            )
            log.insert_record()
        except Exception as e:
            self.logger.exception("Error occurred while inserting log in db {}".format(e))

    def parse_mobile_number(self, mobile_number):
        """
        if mobile number has `+` in it, then slice `+` and return mobile number.
        :param mobile_number:
        """
        if mobile_number.startswith('+'):
            return mobile_number[1:]
        return mobile_number

    def send_sms(self, mobile_number, message=''):
        """
        request synapse given url with required payload for sending simple sms
        """
        response = None
        mobile_number = self.parse_mobile_number(mobile_number)
        payload = {
            "source": self.SOURCE,
            "destination": [mobile_number],
            "text": message
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = communicator.communicate(
                endpoint=self.SEND_SMS_URL,
                method_type=self.REQUEST_METHOD,
                payload=payload,
                auth=HTTPBasicAuth(self.USER_NAME, self.PASSWORD),
                headers=headers
            )
            response.raise_for_status()
            response_json = response.json()
            if response_json[0]['ErrorCode'] != 0:
                raise Exception("Invalid Error Code")
            self.logger.info(json.dumps(response_json))
        except:
            self.logger.exception(json.dumps(response_json))
            self.log_in_db(
                self.SEND_SMS_URL,
                'POST',
                payload,
                headers,
                response.json(),
                response.status_code
            )


global_sms = GlobalSms()
