"""
LMS Manager
"""
import json
import time
from datetime import datetime, timedelta

import requests
from flask import current_app, g, request

from common.api_utils import get_logger, get_api_configurations
from common.constants import AED, DEFAULT_DATETIME_FORMAT, BUSINESS_TRIGGERS_FOR_TAX_DEDUCTION, ADR
from models.aldar_app.api_error_logs import ApiErrorLog
from models.aldar_app.earn import Earn
from models.aldar_app.earn_addendum import EarnAddendum
from models.aldar_app.refund import Refund
from models.aldar_app.transaction_burn import TransactionBurn
import redis

from models.entertainer_web.api_configuration import ApiConfiguration

cache = g.cache


class LMSManager(object):
    logger = get_logger('lms_manager/lms_manager.log.log', 'lms_logger')
    _redis = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'], db=0,
                         password=current_app.config['REDIS_PASSWORD'])
    LMS_TOKEN_LOCK = 'lms_token_lock_{}'.format(current_app.config['ENV'])
    LMS_ACCESS_TOKEN = 'lms_access_token_{}'.format(current_app.config['ENV'])
    LMS_EXPIRATION = 'lms_expiration_time_{}'.format(current_app.config['ENV'])

    @classmethod
    def log_in_db(cls, endpoint, method, request_body, request_header, response_body, http_error_code):
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
                company='LMS',
                error_message="",
                consumer_ip=request.remote_addr
            )
            log.insert_record()
        except Exception as e:
            cls.logger.exception("Error occurred while inserting log in db {}".format(e))

    @classmethod
    def get_lms_token(cls):
        """
        Returns LMS API Token
        """
        try:
            while int((cls._redis.get(cls.LMS_TOKEN_LOCK) or b"").decode() or 0):
                time.sleep(3)
            if (cls._redis.get(cls.LMS_ACCESS_TOKEN) or b"").decode() and \
                    datetime.strptime((cls._redis.get(cls.LMS_EXPIRATION) or b"").decode(),
                                      DEFAULT_DATETIME_FORMAT) > datetime.now():
                return (cls._redis.get(cls.LMS_ACCESS_TOKEN) or b"").decode()
            cls._redis.set(cls.LMS_TOKEN_LOCK, 1)
            payload = {
                'grant_type': current_app.config['LMS_GRANT_TYPE'],
                'username': current_app.config['LMS_USER_NAME'],
                'password': current_app.config['LMS_PASSWORD'],
            }
            headers = {
                'Authorization': "Basic {}".format(current_app.config['LMS_BASIC_AUTH'])
            }

            response = requests.post(
                current_app.config['LMS_AUTH_URL'],
                headers=headers,
                data=payload
            )
            try:
                response.raise_for_status()
            except requests.RequestException:
                cls.log_in_db(
                    current_app.config['LMS_AUTH_URL'],
                    'POST',
                    payload,
                    headers,
                    response.json(),
                    response.status_code
                )
                raise
            access_token = response.json()['access_token']
            expires_in = response.json()['expires_in'] - 60  # seconds
            cls._redis.set(cls.LMS_ACCESS_TOKEN, access_token)
            cls._redis.set(cls.LMS_EXPIRATION, (datetime.now() + timedelta(seconds=expires_in)).strftime(
                DEFAULT_DATETIME_FORMAT))
            cls._redis.set(cls.LMS_TOKEN_LOCK, 0)
            return access_token
        except Exception as e:
            cls.logger.error("Unable to get new LMS token: {}".format(e))
            cls._redis.set(cls.LMS_TOKEN_LOCK, 0)

    @classmethod
    def generate_headers(cls, channel_id='app'):
        return {
            'Authorization': 'Bearer {}'.format(cls.get_lms_token()),
            'Content-Type': 'application/json',
            'channel-id': channel_id
        }

    @classmethod
    def register_user(cls, external_user_id, first_name, last_name, membership_number,  email, mobile_number,
                      registration_date, referrer_member_id, additional_info=None):
        """
        Register User on LMS
        :param registration_date:
        :param membership_number:
        :param external_user_id:
        :param datetime.datetime dob:
        :param first_name:
        :param last_name:
        :param email:
        :param mobile_number:
        :param referrer_member_id:
        :param additional_info:
        """
        if additional_info is None:
            additional_info = {}
        try:
            body = {
                    "external_user_id": external_user_id,
                    "country_of_residence": "AE",
                    "nationality": "AE",
                    "first_name": first_name,
                    "last_name": last_name,
                    "gender": "M",
                    "membership_number": membership_number,
                    "language": "EN",
                    "email": email,
                    "mobile_number": mobile_number.lstrip('+'),
                    "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "additionalInfo": additional_info
                }
            if referrer_member_id:
                body["referrer_member_id"] = referrer_member_id

            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_ENROLLMENT_API'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json['profile']
        except requests.exceptions.RequestException as exception_occurred:
            if exception_occurred.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.logger.exception("Error occurred while enrolling user: {}".format(exception_occurred.response.json()))
            cls.log_in_db(
                current_app.config['LMS_ENROLLMENT_API'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
            raise
        except Exception as e:
            cls.logger.exception("Error occurred while enrolling user: {}".format(e))
            raise

    @classmethod
    def update_lms_user(cls, lms_member_id, gender, nationality, dob):
        """
        Updates LMS User
        :param lms_member_id:
        :param gender:
        :param nationality:
        :param dob:
        """
        try:
            body = {
                    "member_id": lms_member_id,
                    "country_of_residence": nationality,
                    "nationality": nationality,
                    "gender": gender[0].upper(),
                    "date_of_birth": dob.strftime("%Y-%m-%d")
                }
            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_USER_UPDATE_API'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_USER_UPDATE_API'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while updating user: {}".format(e))
            raise

    @classmethod
    def update_lms_user_country_of_residence(cls, lms_member_id, country_of_residence):
        """
        Updates LMS User
        :param country_of_residence:
        :param lms_member_id:
        """
        try:
            body = {
                    "member_id": lms_member_id,
                    "country_of_residence": country_of_residence,
                }
            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_USER_UPDATE_API'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_USER_UPDATE_API'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while updating user: {}".format(e))
            raise

    @classmethod
    def update_lms_user_mobile_number(cls, lms_member_id, mobile_number):
        """
        Updates LMS User Mobile Number
        :param mobile_number:
        :param lms_member_id:
        """
        try:
            body = {
                "member_id": lms_member_id,
                "mobile_number": mobile_number,
            }
            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_USER_UPDATE_API'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_USER_UPDATE_API'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while updating user: {}".format(e))
            raise

    @classmethod
    def get_lms_user_profile(cls, lms_member_id):
        """
        Returns LMS user profile
        :param lms_member_id:
        """
        try:
            headers = cls.generate_headers()
            response = requests.get(
                current_app.config['LMS_GET_USER_PROFILE'].format(lms_member_id),
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get('profile', {})
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_GET_USER_PROFILE'].format(lms_member_id),
                'GET',
                {},
                headers,
                e.response.json(),
                e.response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while fetching user: {}".format(e))
            raise

    @classmethod
    def burn_points(cls, lms_member_id, value, business_trigger, business_category, transaction_id, concept_id,
                    concept_name, description, external_user_id=None, external_user_name=None,
                    currency=AED, redemption_mode='points', user_id=0, source='app'):
        """
        Burns points
        :param source:
        :param concept_id:
        :param concept_name:
        :param description:
        :param lms_member_id:
        :param value:
        :param business_trigger:
        :param business_category:
        :param transaction_id:
        :param external_user_id:
        :param external_user_name:
        :param currency:
        :param redemption_mode:
        :param user_id:
        :return:
        """
        burn_transaction = TransactionBurn(
            source=source,
            user_id=user_id,
            business_trigger=business_trigger,
            business_category=business_category,
            concept_id=concept_id,
            concept_name=concept_name,
            description=description,
            redemption_mode=redemption_mode,
            external_transaction_id=transaction_id,
            redemption_value=value,
            currency=currency,
            external_user_id=external_user_id,
            external_user_name=external_user_name
        )
        burn_transaction.insert_record()

        try:
            body = {
                    "member_id": lms_member_id,
                    "redemption_mode": redemption_mode,
                    "business_trigger": business_trigger,
                    "business_category": business_category,
                    "transaction_id": transaction_id,
                    "transacton_id": transaction_id,  # TODO: need to correct this param, lms receives as typo it is.
                    "currency": currency,
                    "value": value,
                    "concept_id": concept_id
                }
            headers = cls.generate_headers(channel_id=source)
            response = requests.post(
                current_app.config['LMS_BURN_POINTS_URL'],
                headers=headers,
                json=body
            )
            response.raise_for_status()

            if response and response.json().get('status') == 0:
                burned = response.json().get('redemption')

                burn_transaction.points_balance = burned.get('points_balance')
                burn_transaction.points_burned = burned.get('points')
                burn_transaction.amount_burned = burned.get('amount')
                burn_transaction.burn_rate = burned.get('burn_rate')
                burn_transaction.lms_redemption_id = burned.get('redemption_id')
                burn_transaction.lms_redemption_reference_code = burned.get('redemption_reference_code')
                burn_transaction.date_created = burned.get('date_created')
                burn_transaction.date_last_updated = datetime.now()
                burn_transaction.update_record()
            else:
                cls.log_in_db(
                    current_app.config['LMS_BURN_POINTS_URL'],
                    'POST',
                    body,
                    headers,
                    response.json(),
                    response.status_code
                )
            return response.json()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_BURN_POINTS_URL'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
            raise
        except Exception as e:
            cls.logger.exception("Error occurred while burning points: {}".format(e))
            raise

    @classmethod
    def earn(cls, data):
        """
        request lms to earn points
        :param dict data: request data
        """
        transaction_data = data[0]
        # Tax deduction logic resides here
        vat_percentage, service_charges_percentage, vat, service_charges, tax_deduction = None, None, None, None, False
        if transaction_data.get('source') != "CLO" and\
                transaction_data['business_trigger'] in BUSINESS_TRIGGERS_FOR_TAX_DEDUCTION:
            tax_deduction = True
            configs = get_api_configurations(ADR, current_app.config.get('ENV'), ApiConfiguration.PRIVATE)
            vat_percentage = float(configs[ApiConfiguration.VALUE_ADDED_TAX_PERCENTAGE])
            service_charges_percentage = float(configs[ApiConfiguration.SALES_TAX_PERCENTAGE])
            original_value = transaction_data['paid_amount']
            vat = round(original_value - round((original_value / (1 + vat_percentage/100)), 6), 6)
            vat_deducted_value = original_value - vat
            service_charges = round(vat_deducted_value - round((vat_deducted_value / (1 + service_charges_percentage/100)), 6), 6)
            service_charges_deducted_value = round(vat_deducted_value - service_charges, 2)
            # setting new values
            transaction_data['paid_amount'] = service_charges_deducted_value
            transaction_data['net_amount'] = service_charges_deducted_value
            transaction_data['gross_total_amount'] = original_value

        earn_transaction = Earn(
            source=transaction_data.get('source', 'app'),
            user_id=transaction_data['aldar_user_id'],
            business_trigger=transaction_data['business_trigger'],
            business_category=transaction_data['business_category'],
            concept_id=transaction_data['concept_id'],
            concept_name=transaction_data['concept_name'],
            external_transaction_id=transaction_data['external_transaction_id'],
            gross_total_amount=transaction_data['gross_total_amount'],
            net_amount=transaction_data['net_amount'],
            # amount_paid_using_points=transaction_data['gross_total_amount'],
            paid_amount=transaction_data['paid_amount'],
            # redemption_reference=transaction_data['external_transaction_id'],
            currency=transaction_data['currency'],
            charge_id=transaction_data['charge_id'],
            description=transaction_data['description'],
            transaction_datetime=transaction_data['transaction_datetime'],
            external_user_id=transaction_data.get('external_user_id'),
            external_user_name=transaction_data.get('external_user_name')

        )
        earn_transaction.insert_record()

        try:
            headers = cls.generate_headers(channel_id=transaction_data.get('source', 'app'))
            response = requests.post(
                current_app.config['LMS_EARN_POINTS_URL'],
                json=data,
                headers=headers,
            )
            try:
                if tax_deduction:
                    earn_addendum = EarnAddendum(
                        earn_id=earn_transaction.id,
                        value_added_tax=vat,
                        service_charges=service_charges,
                        vat_percentage=vat_percentage,
                        sales_tax_percentage=service_charges_percentage
                    )
                    earn_addendum.insert_record()
            except Exception as e:
                cls.logger.error("Unable to log into earn_addendum: {}".format(e))
            response.raise_for_status()

            if response.json().get('status') == 0:
                earned = response.json().get('batch_earn', {}).get('success', [])

                earn_transaction.points_earned = earned[0].get('earned_points')
                earn_transaction.lms_earn_transaction_id = earned[0].get('earn_transaction_id')
                earn_transaction.earn_rate = earned[0].get('earn_rate')
                earn_transaction.bonus_points = earned[0].get('bonus_points')
                earn_transaction.referrer_bonus_points = sum(earned[0].get('referrer_bonus_points'))
                earn_transaction.member_tier = earned[0].get('member_tier')
                earn_transaction.tier_updated = int(earned[0].get('tier_updated'))
                earn_transaction.creation_date = datetime.now()
                earn_transaction.date_last_updated = datetime.now()
                earn_transaction.update_record()
            else:
                cls.log_in_db(
                    current_app.config['LMS_EARN_POINTS_URL'],
                    'POST',
                    data,
                    headers,
                    response.json(),
                    response.status_code
                )
            json_response = response.json()
            json_response.update(earn_id=earn_transaction.id)
            return json_response
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_EARN_POINTS_URL'],
                'POST',
                data,
                headers,
                response.json(),
                response.status_code
            )
            raise
        except Exception as e:
            cls.logger.exception("Error occurred while requesting an earn: {}".format(e))
            raise

    @classmethod
    def get_lms_user_transactions(cls, lms_member_id, transaction_type='all'):
        """
        Returns LMS user transactions
        :param transaction_type:
        :param lms_member_id:
        """
        try:
            body = {
                    "member_id": lms_member_id,
                    "transaction_type": transaction_type,
                }
            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_GET_USER_TRANSACTIONS'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get('transactions', {})
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_GET_USER_TRANSACTIONS'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while fetching user: {}".format(e))
            raise

    @classmethod
    def get_user_points(cls, lms_member_id, business_trigger, business_category):
        """
        returns lms user's points info
        :param str lms_member_id: member_id
        :param dict business_trigger:
        :param dict business_category:
        """
        try:
            body = {
                "member_id": lms_member_id,
                "business_trigger": business_trigger,
                "business_category": business_category
            }
            headers = cls.generate_headers()
            response = requests.post(
                current_app.config['LMS_GET_POINTS_URL'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get('point_summary', {})
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_GET_POINTS_URL'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
            raise
        except Exception as e:
            cls.logger.exception("Error occurred while requesting an earn: {}".format(e))
            raise

    @classmethod
    def get_lms_configs(cls):
        """
        Returns LMS Configs
        """
        try:
            headers = cls.generate_headers()
            response = requests.get(
                current_app.config['LMS_GET_CONFIGS_API'],
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_GET_CONFIGS_API'],
                'GET',
                {},
                headers,
                response.json(),
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while fetching user: {}".format(e))
            raise

    @classmethod
    def refund(cls, member_id, business_category, business_trigger, transaction_id, refund_points_mode, value,
               currency, description, property_net_value=None, external_user_id=0, external_user_name='',
               source="app", concept_id='', concept_name='', user_id=0):
        """
        request lms to refund points/amount
        :param member_id:
        :param description:
        :param value:
        :param business_trigger:
        :param business_category:
        :param transaction_id:
        :param currency:
        :param refund_points_mode:
        :param property_net_value:
        :param external_user_id:
        :param external_user_name:
        :param source:
        :param concept_id:
        :param concept_name:
        :param user_id:
        """
        refund_transaction = Refund(
            source=source,
            business_category=business_category,
            business_trigger=business_trigger,
            transaction_id=transaction_id,
            refund_points_mode=refund_points_mode,
            refund_amount=value,
            currency=currency,
            description=description,
            user_id=user_id,
            external_user_id=external_user_id,
            external_user_name=external_user_name,
            concept_id=concept_id,
            concept_name=concept_name
        )
        refund_transaction.insert_record()

        try:
            body = {
                "member_id": member_id,
                "business_category": business_category,
                "business_trigger": business_trigger,
                "transaction_id": transaction_id,
                "refund_points_mode": refund_points_mode,
                "value": value,
                "currency": currency,
                "description": description
            }
            # adding property net value against `sales` category
            if property_net_value:
                body['property_net_value'] = property_net_value
                refund_transaction.property_net_value = property_net_value

            headers = cls.generate_headers(channel_id=source)
            response = requests.post(
                current_app.config['LMS_REFUND_URL'],
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            if response.json().get('status') == 0:
                refunded = response.json().get('refund')
                refund_transaction.points_balance = refunded.get('points_balance')
                refund_transaction.points_refunded = refunded.get('points')
                refund_transaction.response_value = refunded.get('value')
            refund_transaction.update_record()

            return response.json().get('refund', {})
        except requests.exceptions.RequestException as e:
            if e.response.status_code == requests.codes.UNAUTHORIZED:
                cls._redis.delete(cls.LMS_ACCESS_TOKEN)
            cls.log_in_db(
                current_app.config['LMS_REFUND_URL'],
                'POST',
                body,
                headers,
                response.json(),
                response.status_code
            )
            raise
        except Exception as e:
            cls.logger.exception("Error occurred while requesting refund: {}".format(e))
            raise


lms_manager = LMSManager()
