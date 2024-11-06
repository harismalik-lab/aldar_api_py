"""
This module contains Rest API Communicator
"""
import json

import requests
from werkzeug.exceptions import InternalServerError

from common.api_utils import get_logger


class Communicator:
    logger = get_logger('communicator/communicator.log', 'communicator_logger')

    @classmethod
    def get_standard_headers(cls, bearer_token):
        """
        Returns standard API headers
        :rtype: dict
        """
        headers = {
            'Authorization': 'Bearer {}'.format(bearer_token),
            'Content-Type': 'application/json'
        }
        return headers

    def communicate(self, endpoint, method_type, params=None, payload=None, bearer_token=None, headers=None, auth=None):
        response = None
        try:
            if method_type.upper() in ('GET', 'POST', 'PUT'):
                method = getattr(requests, method_type.lower())
                _headers = {}
                if bearer_token:
                    _headers = self.get_standard_headers(bearer_token)
                if headers:
                    _headers.update(headers)
                response = method(
                    endpoint,
                    params=params,
                    headers=_headers,
                    data=json.dumps(payload),
                    auth=auth,
                    verify=False
                )
                response.raise_for_status()
            else:
                self.logger.exception("Invalid 'method_type': {} passed for {} with {}".format(
                    method_type,
                    endpoint,
                    payload
                ))
                raise InternalServerError('Unsupported method_type')
        except requests.exceptions.RequestException as exception_occurred:
            self.logger.exception("Error occurred while making request to {} with {}: {}".format(
                endpoint,
                params or payload,
                exception_occurred
            ))
            raise
        return response


communicator = Communicator()
