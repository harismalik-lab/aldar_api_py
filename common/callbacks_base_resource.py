"""
This module contains base resource specific to lms
"""
import json
import uuid

from flask import current_app, request
from flask_restful import Resource
from requests import codes
from werkzeug.exceptions import BadRequest, Unauthorized

from common.api_utils import get_api_configurations, get_logger
from common.constants import ADR, CLO, INTERNAL_SERVER_ERROR
from common.exceptions import InvalidConfigResource
from models.aldar_app.api_error_logs import ApiErrorLog
from models.aldar_app.incoming_api_logs import IncomingApiLogs
from models.db import db
from user_authentication.lms_authentication import token_decorator, HTTPBasicAuthThirdParty

token_decorator = getattr(current_app, 'token_decorator', token_decorator)
basic_auth = getattr(current_app, 'basic_auth', HTTPBasicAuthThirdParty())


@basic_auth.get_password
def get_basic_auth_password(username):
    try:
        return current_app.config['BASIC_AUTH_CREDENTIALS'].get(username)
    except KeyError:
        return None


class CallbacksBaseResource(Resource):

    logger_info = {}
    logger = None
    request_parser = None
    response = {}
    status_code = 200
    code = 0
    send_response_flag = False
    api_version = 'v1'
    log_request = False
    override_status_code = None
    log_api_request = False

    validators = [token_decorator]

    def log_request_in_db(self, error_message=""):
        """
        This method will log API request in db
        """
        if self.log_request:
            try:
                log = ApiErrorLog(
                    company='', # TODO
                    consumer_ip=request.remote_addr,
                    endpoint=request.path,
                    method=request.method,
                    request_body=request.data.decode().replace("\t", "").replace('\n', ''),
                    request_header=json.dumps(dict(request.headers)),
                    response_body=json.dumps(self.response),
                    http_error_code=self.status_code,
                    error_message=error_message
                )
                log.insert_record()
            except Exception as e:
                self.logger.exception("Error occurred while logging request: {}".format(e))

    def log_incoming_clo_request_in_db(self, *args, **kwargs):
        """
        This method will log API request in db
        """
        if self.log_api_request:
            try:
                log = IncomingApiLogs(
                    source=CLO,
                    client_ip=request.remote_addr,
                    endpoint=request.path,
                    membership_id=request.json.get('membership_code'),
                    transaction_id=kwargs.get('transaction_id'),
                    headers=json.dumps(dict(request.headers)),
                    body=request.data.decode().replace("\t", "").replace('\n', '')
                )
                log.insert_record()
            except Exception as e:
                self.logger.exception("body: {}".format(request.data.decode()))
                self.logger.exception("Error occurred while logging request: {}".format(e))

    def get_logger(self):
        """
        Get log instance with given params
        :Raises: Exception when filename is missing.
        """
        if not self.logger and self.logger_info:
            try:
                self.logger = get_logger(
                    filename=self.logger_info.get('filename'),
                    name=self.logger_info.get('name', str(uuid.uuid4()))
                )
            except KeyError:
                raise InvalidConfigResource('filename missing for logs.')

    @classmethod
    def generate_response_dict(cls, message='success', data=None, custom_code=0, success_flag=True):
        """
        Generates response dict from passed parameters
        :param str message: Message
        :param None|dict|list|str data: Data
        :param int custom_code: API custom error code
        :param bool success_flag: Success flag
        :rtype: dict
        """
        response_dict = {
            'success': success_flag,
            'message': message,
            'status_code': custom_code
        }
        if data is not None:
            response_dict['data'] = data
        return response_dict

    def send_response(self, data, status_code):
        """
        :param data: http response-data
        :param status_code: http-status-code
        :return: data, status
        """
        if isinstance(data, str):
            message = data
            data = dict()
            data['message'] = message
        # data['cmd'] = request.full_path
        data['http_response'] = status_code
        if 'status_code' not in data.keys():
            if self.code == codes.UNAUTHORIZED:
                data['status_code'] = -1
        if not data.get('data'):
            data['data'] = {}
        if self.override_status_code is not None:
            data['status_code'] = self.override_status_code
        return data, status_code

    def process_bad_request(self, exception_raised=None):
        """
        Process the bad request exception of http-view
        :return: http-response
        """
        self.override_status_code = 1
        message = getattr(exception_raised, 'data', {}).get('message', exception_raised.description)
        if isinstance(message, dict):
            for exception_field, exception_message in message.items():
                message = '{field}: {message}'.format(field=exception_field, message=exception_message)
                if exception_message.startswith('Missing required parameter in'):
                    message = '{field}: missing required parameter'.format(field=exception_field)
                break
        if not getattr(exception_raised, 'data', {}):
            setattr(exception_raised, 'data', {})
        exception_raised.data['message'] = message
        return self.process_request_exception(exception_raised=exception_raised)

    def process_request_exception(
            self,
            exception_raised=None,
            code=None,
            status_code=None,
            message=INTERNAL_SERVER_ERROR
    ):
        """
        Process the general exception of http-view
        :return: http-response
        """
        if not self.logger:
            self.get_logger()
        if current_app.config['DEBUG']:
            if exception_raised:
                raise exception_raised
        self.code = 500
        self.status_code = 500
        if exception_raised:
            if getattr(exception_raised, 'data', None):
                message = exception_raised.data.get('message', exception_raised.data)
            elif getattr(exception_raised, 'description', None):
                message = exception_raised.description
            self.status_code = getattr(exception_raised, 'code', 500)
            self.code = getattr(exception_raised, 'code', 500)
        if self.logger:
            if not getattr(self, 'request_args', None):
                request_params = request.values.to_dict()
            else:
                request_params = self.request_args
            self.logger.exception(
                'Exception occurred with url:{full_url} params:{params} message:{message}'.format(
                    message=message,
                    full_url=request.path,
                    params=request_params
                )
            )
            self.remove_logger_handlers()
        if current_app.config['DEBUG'] and exception_raised:
            raise exception_raised
        self.response = {
            "message": message,
            'success': False
        }
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        # logging in db
        self.log_request_in_db(message)
        if isinstance(exception_raised, Unauthorized):
            self.response['status_code'] = -1
        return self.send_response(self.response, self.status_code)

    def remove_logger_handlers(self):
        if self.logger:
            for handler in getattr(self.logger, 'handlers', []):
                if not current_app.config.get('GENERATE_APM_ERROR_LOGS', False):
                    handler.stream.close()
                self.logger.removeHandler(handler)

    def populate_request_arguments(self):
        """
        Set the class arguments using request_parser.
        """
        pass

    def process_request(self, *args, **kwargs):
        """
        Business logic goes here.
        """
        self.send_response_flag = True
        pass

    def set_response(self, response, code=None):
        """
        Set class attributes response along with send_response_flag.
        """
        if code:
            self.code = code
        self.send_response_flag = True
        self.response = response

    def is_send_response_flag_on(self):
        """
        :return: True if send_response_flag is on.
        """
        return self.send_response_flag

    def pre_processsing(self):
        """
        Pre-processing.
        """
        self.get_logger()

    def request_flow(self, *args, **kwargs):
        """
        Http Request flow.
        """
        self.pre_processsing()
        configs = get_api_configurations(ADR, environment=current_app.config.get('ENV'))
        self.log_api_request = configs.get('log_api_request') and self.log_api_request
        if self.log_api_request:
            self.log_incoming_clo_request_in_db(*args, **kwargs)
        self.request_args = None
        try:
            if self.request_parser:
                self.request_args = self.request_parser.parse_args()
        except BadRequest as bad_request_exception:
            return self.process_bad_request(exception_raised=bad_request_exception)

        try:
            if self.request_args:
                self.populate_request_arguments()
            self.process_request(*args, **kwargs)
            if self.send_response_flag:
                return self.send_response(self.response, self.status_code)
        except Exception as exception_raised:
            return self.process_request_exception(exception_raised=exception_raised)
        finally:
            try:
                db.session.close()
                db.session.remove()
                db.engine.dispose()
            except Exception as e:
                self.logger.exception("Error occurred while releasing db resources: {}".format(e))
            if self.logger:
                self.remove_logger_handlers()


class BasePostResource(CallbacksBaseResource):

    def post(self, *args, **kwargs):
        """
        Post request handler.
        """
        method_reference = self.request_flow
        for validator in self.validators:
            method_reference = validator(self.request_flow)
        return method_reference(self, *args, **kwargs)


class BaseGetResource(CallbacksBaseResource):

    def get(self, *args, **kwargs):
        """
        Get request handler.
        """
        method_reference = self.request_flow
        for validator in self.validators:
            method_reference = validator(self.request_flow)
        return method_reference(self, *args, **kwargs)


class BasePutResource(CallbacksBaseResource):

    def put(self, *args, **kwargs):
        """
        Put request handler.
        """
        method_reference = self.request_flow
        for validator in self.validators:
            method_reference = validator(self.request_flow)
        return method_reference(self, *args, **kwargs)
