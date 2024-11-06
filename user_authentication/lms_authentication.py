"""
LMS Authentication Logic reside here for
"""
from flask import request, current_app
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended.exceptions import InvalidHeaderError, NoAuthorizationError
from flask_jwt_extended.view_decorators import ctx_stack, wraps
from jwt import InvalidAlgorithmError
from jwt.exceptions import InvalidSignatureError
from werkzeug.datastructures import Authorization
from werkzeug.exceptions import Forbidden, Unauthorized

from models.entertainer_web.api_tokens import ApiTokens
from user_authentication.constants import (
    INVALID_JWT,
    JWT_HEADER_ERROR_MESSAGE,
    JWT_SIGNATURE_MISMATCH,
    MISSING_JWT_ERROR_MESSAGE
)


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

        data = get_jw_token_identity()
        if data and data.get('company'):
            return fn(self, *args, **kwargs)
        if data and data.get('error_msg'):
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


def get_verified_jwt_payload():
    jwt_bearer = request.environ.get('HTTP_AUTHORIZATION')
    if jwt_bearer:
        token = jwt_bearer.split(' ')[1]
        data = ApiTokens.validate_token(token)
        if data:
            return {'company': data.company}
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


class HTTPBasicAuthThirdParty(HTTPBasicAuth):

    def login_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_app.config.get('BASIC_AUTH_ENABLED_TO_GET_ACCESS_TOKEN', False):
                return f(*args, **kwargs)
            auth = request.authorization
            # To avoid circular import
            # from web_api.sharing.api import PostSharingSendApi
            # if isinstance(args[0], PostSharingSendApi):
            #     return f(*args, **kwargs)
            if auth is None and 'Authorization' in request.headers:
                # Flask/Werkzeug do not recognize any authentication types
                # other than Basic or Digest, so here we parse the header by
                # hand
                try:
                    auth_type, token = request.headers['Authorization'].split(
                        None, 1)
                    auth = Authorization(auth_type, {'token': token})
                except ValueError:
                    # The Authorization header is either empty or has no token
                    pass

            # if the auth type does not match, we act as if there is no auth
            # this is better than failing directly, as it allows the callback
            # to handle special cases, like supporting multiple auth types
            if auth is not None and auth.type.lower() != self.scheme.lower():
                auth = None

            # Flask normally handles OPTIONS requests on its own, but in the
            # case it is configured to forward those to the application, we
            # need to ignore authentication headers and let the request through
            # to avoid unwanted interactions with CORS.
            if request.method != 'OPTIONS':  # pragma: no cover
                if auth and auth.username:
                    password = self.get_password_callback(auth.username)
                else:
                    password = None
                if not self.authenticate(auth, password):
                    # Clear TCP receive buffer of any pending data
                    return self.auth_error_callback()

            return f(*args, **kwargs)
        return decorated
