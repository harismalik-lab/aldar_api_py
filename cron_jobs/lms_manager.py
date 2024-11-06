"""
LMS Manager
"""
import json
import os
import time

import requests

from cron_jobs.helper import get_logger
# from models.aldar_app.api_error_logs import ApiErrorLog


class LMSManager(object):
    base_dir = os.path.dirname(__file__)
    logger = get_logger(base_dir, 'logs/lms_manager.log.log', 'lms_logger')

    def __init__(self, lms_grant_type, lms_user_name, lms_password, lms_basic_auth, lms_auth_url):
        self.lms_grant_type = lms_grant_type
        self.lms_user_name = lms_user_name
        self.lms_password = lms_password
        self.lms_basic_auth = lms_basic_auth
        self.lms_auth_url = lms_auth_url
        self.lms_access_token = self.get_lms_access_token()

    def log_in_db(self, endpoint, method, request_body, request_header, response_body, http_error_code):
        """
        Logs LMS error in db
        """
        try:
            log = ApiErrorLog(
                endpoint=endpoint,
                method=method,
                request_body=json.dumps(request_body),
                request_header=json.dumps(request_header),
                response_body=json.dumps(response_body),
                http_error_code=http_error_code,
                company='LMS'
            )
            log.insert_record()
        except Exception as e:
            self.logger.exception("Error occurred while inserting log in db {}".format(e))

    def get_lms_access_token(self):
        """
        Returns LMS API Token
        """
        payload = {
            'grant_type': self.lms_grant_type,
            'username': self.lms_user_name,
            'password': self.lms_password,
        }
        headers = {
            'Authorization': "Basic {}".format(self.lms_basic_auth)
        }

        response = requests.post(
            self.lms_auth_url,
            headers=headers,
            data=payload
        )
        try:
            response.raise_for_status()
        except requests.RequestException:
            self.log_in_db(
                self.lms_auth_url,
                'POST',
                payload,
                headers,
                response.json(),
                response.status_code
            )
            raise
        return response.json()['access_token']

    def earn(self, data, lms_earn_points_url, _access_token_refresh_required_count=0):
        """
        request lms to earn points
        :param list data: request data
        :param str lms_earn_points_url: LMS earn point url
        :param bool _access_token_refresh_required_count: if lms token expired and this is less then 5 then call get
        new lms access token and call again this method for earn api
        """
        headers = {
            'Authorization': 'Bearer {}'.format(self.lms_access_token),
            'Content-Type': 'application/json',
            'channel-id': 'sftp'
        }
        try:
            response = requests.post(
                lms_earn_points_url,
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            self.log_in_db(
                lms_earn_points_url,
                'POST',
                data,
                request_header=headers,
                response_body=response.json(),
                http_error_code=response.status_code
            )
            if response.status_code == requests.codes.unauthorized:
                _access_token_refresh_required_count += 1
                if _access_token_refresh_required_count < 5:
                    time.sleep(15)
                    self.lms_access_token = self.get_lms_access_token()
                    return self.earn(data, lms_earn_points_url, _access_token_refresh_required_count)
                else:
                    raise Exception('Could not get valid LMS access token for earn api')
            else:
                return response.json()
        except Exception as e:
            self.logger.exception("Error occurred while requesting an earn: {}".format(e))
            raise

    def refund(self, data, lms_refund_api_url, _access_token_refresh_required_count=0):
        """
        request lms to earn points
        :param dict data: request data
        :param str lms_refund_api_url: LMS earn point url
        :param bool _access_token_refresh_required_count: if lms token expired and this is less then 5 then call get
        new lms access token and call again this method for refund api
        """
        headers = {
            'Authorization': 'Bearer {}'.format(self.lms_access_token),
            'Content-Type': 'application/json',
            'channel-id': 'sftp'
        }
        try:
            response = requests.post(
                lms_refund_api_url,
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            self.log_in_db(
                lms_refund_api_url,
                'POST',
                data,
                request_header=headers,
                response_body=response.json(),
                http_error_code=response.status_code
            )
            if response.status_code == requests.codes.unauthorized:
                _access_token_refresh_required_count += 1
                if _access_token_refresh_required_count < 5:
                    time.sleep(15)
                    self.lms_access_token = self.get_lms_access_token()
                    return self.refund(data, lms_refund_api_url, _access_token_refresh_required_count)
                else:
                    raise Exception('Could not get valid LMS access token for refund api')
            else:
                return response.json()
        except Exception as e:
            self.logger.exception("Error occurred while requesting an refund: {}".format(e))
            raise

    def register_user(self, lms_enrollment_api, external_user_id, first_name, last_name, membership_number,  email,
                      mobile_number, registration_date, referrer_member_id, country_of_residence, nationality,
                      gender, date_of_birth, additional_info=None, _access_token_refresh_required_count=0):
        """

        :param lms_enrollment_api:
        :param external_user_id:
        :param first_name:
        :param last_name:
        :param membership_number:
        :param email:
        :param mobile_number:
        :param registration_date:
        :param referrer_member_id:
        :param country_of_residence:
        :param nationality:
        :param gender:
        :param date_of_birth:
        :param additional_info:
        :param bool _access_token_refresh_required_count: if lms token expired and this is less then 5 then call get
        new lms access token and call again this method for register user
        :return:
        """
        headers = {
            'Authorization': 'Bearer {}'.format(self.lms_access_token),
            'Content-Type': 'application/json',
            'channel-id': 'fallback-job'
        }
        if additional_info is None:
            additional_info = {}
        try:
            body = {
                "external_user_id": external_user_id,
                "first_name": first_name,
                "last_name": last_name,
                "membership_number": membership_number,
                "language": "EN",
                "email": email,
                "mobile_number": mobile_number.lstrip('+'),
                "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
                "additionalInfo": additional_info
            }
            if date_of_birth:
                body.update(date_of_birth=date_of_birth)
            if country_of_residence:
                body.update(country_of_residence=country_of_residence)
            else:
                body.update(country_of_residence='AE')
            if nationality:
                body.update(nationality=nationality)
            if gender:
                if gender.lower() == 'male':
                    body.update(gender='M')
                elif gender.lower() == 'female':
                    body.update(gender='F')
                else:
                    body.update(gender=gender)
            if referrer_member_id:
                body["referrer_member_id"] = referrer_member_id

            response = requests.post(
                lms_enrollment_api,
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json['profile']
        except requests.exceptions.RequestException:
            if response.status_code == requests.codes.unauthorized:
                _access_token_refresh_required_count += 1
                if _access_token_refresh_required_count < 5:
                    time.sleep(15)
                    self.lms_access_token = self.get_lms_access_token()
                    return self.register_user(lms_enrollment_api, external_user_id, first_name, last_name,
                                              membership_number,  email, mobile_number, registration_date,
                                              referrer_member_id, country_of_residence, nationality, gender,
                                              date_of_birth, additional_info=None,
                                              _access_token_refresh_required_count=_access_token_refresh_required_count)
                else:
                    raise Exception('Could not get valid LMS access token for enrolling user api')
            else:
                raise
        except Exception as e:
            self.logger.exception("Error occurred while enrolling user: {}".format(e))
            raise
