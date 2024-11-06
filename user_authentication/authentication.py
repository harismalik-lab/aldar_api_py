"""
Authentication Logics reside here
"""
import json
import time
from base64 import b64decode

from flask import request, current_app
from flask_jwt_extended.exceptions import InvalidHeaderError, NoAuthorizationError
from flask_jwt_extended.view_decorators import ctx_stack, wraps
from jwt import InvalidAlgorithmError, decode
from jwt.exceptions import InvalidSignatureError
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized

from common.constants import ADR, INVALID_TOKEN
from models.aldar_app.user import User
from models.consolidation.ent_customer_profile import EntCustomerProfile
from models.entertainer_web.session import Session
from models.entertainer_web.wl_product import WlProduct
from models.entertainer_web.wl_user_group import WlUserGroup
from models.entertainer_web.wlvalidation import Wlvalidation
from user_authentication.constants import (INVALID_JWT, JWT_HEADER_ERROR_MESSAGE, JWT_SIGNATURE_MISMATCH,
                                           MISSING_JWT_ERROR_MESSAGE)


def token_decorator(fn):
    @wraps(fn)
    def validator(self, *args, **kwargs):
        return jwt_handler(fn)(self, *args, **kwargs)
    return validator


def get_jw_token_identity():
    """
    Returns JWT identity
    """
    return getattr(ctx_stack.top, 'jwt_identity', {})


def get_current_customer():
    """
    Return the customer's session-data.
    """
    return getattr(ctx_stack.top, 'session_data', {"company": ADR})


def jwt_handler(fn):
    """
    If you decorate a vew with this, it will ensure that the requester has a
    valid JWT before calling the actual view. This does not check the freshness
    of the token.
    See also: fresh_jwt_required()
    :param fn: The view function to decorate
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not hasattr(ctx_stack.top, 'jwt_identity'):
            if request.environ.get('HTTP_AUTHORIZATION'):
                jwt_data = decode_jwt_from_header()
                ctx_stack.top.jwt_identity = jwt_data
            else:
                ctx_stack.top.jwt_identity = {}
                return token_required(fn)(self, *args, **kwargs)
        data = get_jw_token_identity()
        if data and data.get('company'):
            return token_required(fn)(self, *args, **kwargs)
        elif data and data.get('error_msg'):
            exception_to_be_raised = Unauthorized("Unauthorized")
            data = data.get('error_msg')
            self.status_code = 401
            self.code = 401
            self.send_response_flag = True
            self.process_request_exception(
                code=self.code,
                status_code=self.status_code,
                message=data,
                exception_raised=exception_to_be_raised
            )
            self.remove_logger_handlers()
            return self.send_response(data, self.status_code)
        # if token is inactive or wrong token
        data = INVALID_JWT
        self.status_code = 403
        self.code = 403
        self.send_response_flag = True
        exception_to_be_raised = Forbidden("You are not allowed to access this application")
        self.process_request_exception(
            code=self.code,
            status_code=self.status_code,
            message=data,
            exception_raised=exception_to_be_raised
        )
        self.remove_logger_handlers()
        return self.send_response(data, self.status_code)
    return wrapper


def token_required(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            jw_data = ctx_stack.top.jwt_identity
            if getattr(self, 'strict_token', False):
                if not jw_data.get('session_token'):
                    raise Forbidden(
                        'A valid "session_token" is required.'
                    )
            if not getattr(self, 'required_token', True) and not request.environ.get('HTTP_AUTHORIZATION'):
                return fn(self, *args, **kwargs)

            company = ADR
            session_token = jw_data.get('session_token')
            session_data = dict()
            session_data['company'] = company
            session_data['is_user_logged_in'] = False
            session_data['is_using_trial'] = False
            session_data['user_id'] = 0
            session_data['customer_id'] = 0
            session_data['email'] = ''

            if session_token:
                # Param Fetcher Object
                if not company:
                    data = INVALID_TOKEN
                    self.status_code = 403
                    self.code = 403
                    self.send_response_flag = True
                    self.process_request_exception(code=self.code, status_code=self.status_code, message=data)
                    self.remove_logger_handlers()
                    return self.send_response(data, self.status_code)
                session = Session.get_by_company_and_session_token(company=company, session_token=session_token)
                if not session:
                    raise Forbidden(
                        'Invalid "session_token" provided.'
                    )
                user_id = session.customer_id
                aldar_user = User.get_active_by_et_id(user_id)
                if not aldar_user:
                    data = INVALID_TOKEN
                    self.status_code = 403
                    self.code = 403
                    self.send_response_flag = True
                    self.process_request_exception(code=self.code, status_code=self.status_code, message=data)
                    self.remove_logger_handlers()
                    return self.send_response(data, self.status_code)
                session_data['aldar_user_id'] = aldar_user.id
                session_data['lms_member_id'] = aldar_user.lms_membership_id
                session_data['email'] = aldar_user.email
                refresh_required = session.refresh_required
                product_ids = session.product_ids
                if refresh_required:
                    try:
                        user_groups = Wlvalidation.get_user_groups(company, session.customer_id)
                        if not user_groups:
                            user_groups = [WlUserGroup.DEFAULT_USER_GROUP]
                        product_ids = WlProduct.get_configured_product_ids(company, user_groups)
                        session.product_ids = ','.join(map(str, product_ids))
                        if product_ids:
                            session.date_cached = time.time()
                            session.refresh_required = 0
                            session.save_changes()
                    except Exception:
                        raise
                session_data['is_user_logged_in'] = True
                session_data['id'] = session.id
                session_data['session_token'] = session.session_token
                session_data['user_id'] = user_id
                session_data['customer_id'] = user_id
                session_data['new_member_group'] = EntCustomerProfile.MEMBERSTATUS_PROSPTECT
                if product_ids:
                    session_data['new_member_group'] = EntCustomerProfile.MEMBERSTATUS_MEMBER
                session_data['member_type_id'] = session_data['new_member_group']
                session_data['member_type'] = EntCustomerProfile.get_member_type(
                    session_data['new_member_group']
                )
                session_data['product_ids'] = list(
                    map(int, session.product_ids.split(','))) if session.product_ids else []
            ctx_stack.top.session_data = session_data
            return fn(self, *args, **kwargs)
        except BadRequest as bad_request_exception:
            return self.process_bad_request(exception_raised=bad_request_exception)
        except Exception as exception_raised:
            return self.process_request_exception(exception_raised=exception_raised)
    return wrapper


def get_verified_jwt_payload():
    jwt_bearer = request.environ.get('HTTP_AUTHORIZATION')
    if jwt_bearer:
        jwt_bearer = jwt_bearer.split(' ')[1]
        header = b64decode(jwt_bearer.split('.')[0])
        jwt_algorithm = json.loads(header.decode()).get('alg')
        secret_key = current_app.config['JWT_SECRET_KEY']
        data = decode(jwt_bearer, secret_key, algorithms=[jwt_algorithm])
        data['company'] = ADR
        return data
    raise InvalidHeaderError


def process_exception(exception_raised, message="Unable to authorize"):
    if getattr(exception_raised, 'data', None):
        message = exception_raised.data.get('message', exception_raised.data)
    elif getattr(exception_raised, 'description', None):
        message = exception_raised.description
    elif getattr(exception_raised, 'args', []):
        message = exception_raised.args[0]
    return message


def decode_jwt_from_header():
    """
    Decodes JWT from authorization header and get identity
    :return: JWT identity or exception if raised
    """
    try:
        data = get_verified_jwt_payload()
    except InvalidHeaderError:
        data = {'error_msg': JWT_HEADER_ERROR_MESSAGE}
    except NoAuthorizationError:
        data = {'error_msg': MISSING_JWT_ERROR_MESSAGE}
    except (InvalidSignatureError, InvalidAlgorithmError):
        data = {'error_msg': JWT_SIGNATURE_MISMATCH}
    except Exception as exception_raised:
        error = process_exception(exception_raised)
        data = {'error_msg': error}
    return data
