"""
This cron will do following tasks
 - fetch user from database where lms membership id and password is null and sync count less then 5
 - Make LMS enrolment api calls for fetched user
    - if response is success then update lms membership id and sync count for user
    - if response is failure then update sync count for user
"""
import datetime
import json
import logging
import os
import sys

import requests
from sqlalchemy import Column, Date, String, Text, create_engine, or_, and_
from sqlalchemy.dialects.mysql import INTEGER, TIMESTAMP, TINYINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

system_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if 'adr_scripts' not in system_path:
    system_path = os.path.join(system_path, 'adr_scripts')
sys.path.append(system_path)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

base_dir_path = os.path.dirname(__file__)
os.makedirs('{}/logs'.format(base_dir_path), exist_ok=True)

from cron_jobs import constants
from cron_jobs.helper import get_logger, from_pyfile
from cron_jobs.lms_manager import LMSManager

DB_URI = ''

LMS_GRANT_TYPE = ''
LMS_BASIC_AUTH = ''
LMS_AUTH_URL = ''
LMS_ENROLLMENT_API = ''
DELAY_BETWEEN_LMS_API_REQUESTS = 0.5                  # in seconds
SFTP_USERS = {}

ERRORS_LOG_FILE_NAME = 'aldar_users_sync_job_errors.log'


def init():
    """
    Initialize sync job settings.
    :return:
    """
    global ERROR_LOGGER
    application_settings_file_name = os.environ.get('APPLICATION_SETTINGS')
    if not application_settings_file_name:
        config_path = '{root}/configs/'.format(root=os.getcwd())
        if 'cron_jobs' not in os.getcwd().lower():
            config_path = '{root}/configs/'.format(root=base_dir_path)
        application_settings_file_name = os.path.join(config_path, 'local_settings.py')
    settings_module = from_pyfile(application_settings_file_name)
    context = dict()
    for setting in dir(settings_module):
        if setting.isupper():
            context[setting] = getattr(settings_module, setting)
    globals().update(context)
    ERROR_LOGGER = get_logger(
        directory='{}/logs'.format(base_dir_path),
        filename=ERRORS_LOG_FILE_NAME,
        name='aldar_user_sync_errors',
        logging_level=logging.INFO
    )


init()


engine = create_engine(DB_URI, echo=False, poolclass=NullPool, isolation_level='READ COMMITTED')
base = declarative_base()
orm_session = sessionmaker(bind=engine)
session = orm_session()


class User(base):
    __tablename__ = 'user'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(100), unique=True)
    password = Column(String(300))
    country_of_residence = Column(String(4))
    nationality = Column(String(4))
    date_of_birth = Column(Date)
    gender = Column(String(10))
    mobile_no = Column(String(20), unique=True)
    et_user_id = Column(INTEGER(11), index=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    is_active = Column(TINYINT(1), index=True)
    is_phone_verified = Column(TINYINT(1), index=True)
    password_reset_token = Column(String(30))
    password_reset_expiry = Column(TIMESTAMP)
    profile_image = Column(String(300))
    lms_membership_id = Column(String(100))
    lms_tier = Column(String(10), nullable=True)
    lms_status = Column(String(20), nullable=True)
    membership_id = Column(String(20), nullable=True)
    enable_email_notification = Column(TINYINT, default=1)
    enable_push_notification = Column(TINYINT, default=1)
    referrer_member_id = Column(String(100))
    sync_attempts = Column(TINYINT, default=0)

    @classmethod
    def get_users_chunk(cls):
        """
        Returns user against email and also if lms_membership_id exists
        :rtype: list
        """
        return session.query(User).filter(
            and_(cls.email != None, cls.email != ''),
            or_(cls.lms_membership_id.is_(None), cls.lms_membership_id == ''),
            cls.sync_attempts < 5
        ).limit(15).all()


class ApiErrorLog(base):
    __tablename__ = 'api_error_logs'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    consumer_ip = Column(String(20), nullable=False, default='')
    company = Column(String(100), nullable=False, index=True, default='')
    endpoint = Column(String(100), nullable=False, index=True, default='')
    method = Column(String(40), nullable=False, default='')
    request_body = Column(Text, nullable=False)
    request_header = Column(Text, nullable=False)
    response_body = Column(Text, nullable=False)
    http_error_code = Column(String(10), nullable=False, default='')
    error_message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.utcnow)


class AldarUserSynchronizer(object):

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
                error_message='',
                company='LMS'
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            ERROR_LOGGER.exception("Error occurred while inserting log in db {}".format(e))

    @classmethod
    def increment_user_sync_attempts(cls, user_id):
        """
        Increments user sync_attempts against user_id
        :param int user_id: User Id
        """
        try:
            session.query(User).filter(User.id == user_id).update({'sync_attempts': User.sync_attempts + 1})
            session.commit()
        except Exception as e:
            ERROR_LOGGER.exception("Error occurred while increment sync_attempts".format(user_id, e))
            raise

    @classmethod
    def mark_user_as_synced(cls, user_id, lms_membership_id, status, tier):
        try:
            if user_id:
                lms_status = status
                if status.lower() != 'active':
                    is_active = 0
                else:
                    is_active = 1
                session.query(User).filter(User.id == user_id).update(
                    {
                        'lms_membership_id': lms_membership_id,
                        'updated_at': datetime.datetime.now(),
                        'sync_attempts': User.sync_attempts + 1,
                        'lms_status': lms_status,
                        'lms_tier': tier,
                        'is_active': is_active
                    },
                )
                session.commit()
        except Exception as e:
            ERROR_LOGGER.exception("Error occurred while marking user: {} as synced: {}".format(user_id, e))
            raise

    @classmethod
    def get_users_to_be_synced(cls):
        users_chunk = User.get_users_chunk()
        return users_chunk

    @classmethod
    def register_user_in_lms(cls, lms_manager, user):
        try:
            response = lms_manager.register_user(
                LMS_ENROLLMENT_API,
                external_user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                membership_number=user.membership_id,
                email=user.email,
                mobile_number=user.mobile_no,
                registration_date=datetime.datetime.now(),
                referrer_member_id=user.referrer_member_id,
                country_of_residence=user.country_of_residence,
                nationality=user.nationality,
                gender=user.gender,
                date_of_birth=user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None
            )
            ERROR_LOGGER.info("Response from LMS: {}".format(response))
            lms_membership_id = response['member_id']
            status = response['status']
            tier = response['member_tier']
            cls.mark_user_as_synced(user.id, lms_membership_id, status, tier)
        except requests.exceptions.RequestException as err:
            errors = err.response.json().get('errors')
            ERROR_LOGGER.exception(
                'Exception occurred in syncing user id = {id}. \n Error details = {error_details} \n '
                'exception details = {exception_details}'.format(
                    id=user.id,
                    error_details=errors,
                    exception_details=err
                )
            )
            cls.log_in_db(
                LMS_ENROLLMENT_API,
                'POST',
                json.loads(err.request.body.decode('utf-8')),
                request_header=dict(err.request.headers),
                response_body=err.response.json(),
                http_error_code=err.response.status_code
            )
            cls.increment_user_sync_attempts(user.id)

    @classmethod
    def sync_users(cls, users):
        lms_manager = LMSManager(
            LMS_GRANT_TYPE,
            SFTP_USERS.get('user_sync_job').get('user_name'),
            SFTP_USERS.get('user_sync_job').get('password'),
            LMS_BASIC_AUTH,
            LMS_AUTH_URL
        )
        for user in users:
            try:
                cls.register_user_in_lms(lms_manager, user)
            except Exception as e:
                ERROR_LOGGER.exception("Error occurred in syncing lms user {}: {}".format(user.id, e))
                cls.increment_user_sync_attempts(user.id)

    @classmethod
    def run(cls):
        users = cls.get_users_to_be_synced()
        users_count = len(users)
        ERROR_LOGGER.info("Syncing {} users".format(users_count))
        if users:
            cls.sync_users(users)


if __name__ == '__main__':
    try:
        AldarUserSynchronizer.run()
    except Exception as err:
        ERROR_LOGGER.exception(
            "Exception occurred in synchronizing user. Error Details are {error_details}".format(
                error_details=err
            )
        )
    finally:
        session.close()
        engine.dispose()
