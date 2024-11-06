"""
Loyalty Facts Manager
"""
import json

import requests
from flask import current_app, g, request
from requests.auth import HTTPBasicAuth

from common.api_utils import get_logger
from models.aldar_app.api_error_logs import ApiErrorLog
from utils.loyalty_facts_constants import TRANSACTION_RESOLVE_DECISIONS, TRANSACTION_RESOLVE_STATUS_CODE_MESSAGES

cache = g.cache


class LoyaltyFactsManager(object):
    logger = get_logger('loyalty_facts_manager/loyalty_facts_manager.log', 'loyalty_facts_manager')

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
                response_body=response_body.decode(),
                http_error_code=http_error_code,
                company='LF',
                error_message="",
                consumer_ip=request.remote_addr
            )
            log.insert_record()
        except Exception as e:
            cls.logger.exception("Error occurred while inserting log in db {}".format(e))

    @classmethod
    def transaction_resolution(cls, transaction_id, decision):
        """
        Resolves CLO transaction
        :param transaction_id:
        :param decision:
        """
        try:
            body = {
                'transactionId': transaction_id,
                'decision': TRANSACTION_RESOLVE_DECISIONS.get(decision),
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(
                current_app.config['LF_BASE_URL'].format(
                    current_app.config['LF_TRANSACTION_RESOLUTION_URL'].format(transactionId=transaction_id)
                ),
                json=body,
                headers=headers,
                cert=(current_app.config['LF_CERT_PATH'], current_app.config['LF_KEY_PATH']),
                auth=HTTPBasicAuth(current_app.config['LF_USERNAME'], current_app.config['LF_PASSWORD'])
            )
            response.raise_for_status()
            response_json = response.json()
            status_msg = TRANSACTION_RESOLVE_STATUS_CODE_MESSAGES.get(int(response_json['statusCode']), "")
            response_json['status_msg'] = status_msg
            return response_json
        except requests.exceptions.RequestException:
            cls.log_in_db(
                current_app.config['LF_BASE_URL'].format(
                    current_app.config['LF_TRANSACTION_RESOLUTION_URL'].format(transactionId=transaction_id)
                ),
                'POST',
                body,
                headers,
                response.content,
                response.status_code
            )
        except Exception as e:
            cls.logger.exception("Error occurred while updating user: {}".format(e))
            raise


loyalty_facts_manager = LoyaltyFactsManager()
