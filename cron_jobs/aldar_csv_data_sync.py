"""
This cron will do following tasks
 - fetch csv files from sftp
 - Process csv
 - save csv records
 - Move processed csv to archived directory if file is error out then move to error directory
 - filter valid records
 - Make LMS api calls for valid record
 - save update record according to lms api data
 - Create log file in csv format on SFTP
"""
import argparse
import csv
import datetime
import json
import logging
import os
import sys
import time
from itertools import repeat
from math import ceil
from random import randint

import gnupg
import pysftp
from marshmallow.validate import ValidationError
from phpserialize import dumps as php_json_dumps
from sqlalchemy import TEXT, Column, Date, DateTime, Float, String, create_engine, func
from sqlalchemy.dialects.mysql import INTEGER, BIT, TIMESTAMP, TINYINT
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
SFTP_SERVER_HOST = ''
SFTP_USER_NAME = ''
SSH_FILE_PATH = ''

LMS_GRANT_TYPE = 'password'
LMS_BASIC_AUTH = ''
LMS_AUTH_URL = ''
LMS_EARN_POINTS_URL = ''
LMS_REFUND_POINTS_URL = ''
CHUNK_SIZE = 1
DELAY_BETWEEN_LMS_API_REQUESTS = 0.5                  # in seconds
ENTERTAINER_PASS_PHRASE = ''
SFTP_USERS = {}

ALDAR_SFTP_FAILURE_TEMPLATE_ID = 983
ALDAR_SFTP_SUCCESS_TEMPLATE_ID = 984


ERRORS_LOG_FILE_NAME = 'aldar_data_sync_job_errors.log'


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
        name='aldar_data_sync_errors',
        logging_level=logging.INFO
    )


init()


LOCAL_FILE_DIR = '{}/downloadeds/{}'.format(
    base_dir_path,
    datetime.datetime.utcnow().strftime('%Y-%m-%d %H-%M-%S')
)
for _dir in constants.ALDAR_DIRECTORIES.keys():
    ALDAR_DOWNLOADED_FOLDER = os.path.join(LOCAL_FILE_DIR, _dir)
    os.makedirs(ALDAR_DOWNLOADED_FOLDER, exist_ok=True)

NEW_GNUPG_HOME = '{}/keys'.format(base_dir_path)

if os.path.exists(NEW_GNUPG_HOME) is True:
    print("The {0} directory already exists.".format(NEW_GNUPG_HOME))
else:
    message = "Aldar PGP keys home directory doesn't exist. Aldar PGP keys directory {aldar_dir}\n".format(
        aldar_dir=NEW_GNUPG_HOME
    )
    ERROR_LOGGER.exception(message)
    raise Exception(message)
try:
    gpg = gnupg.GPG(gnupghome=NEW_GNUPG_HOME)
except OSError as error:
    message = "Aldar can't find gpg binary. Try creating by giving gpg binary path\n".format(
        aldar_dir=NEW_GNUPG_HOME
    )
    ERROR_LOGGER.exception(message)
    gpg = gnupg.GPG(gnupghome=NEW_GNUPG_HOME, gpgbinary="/usr/local/bin/gpg")
    ERROR_LOGGER.info('GPG object initialized by using binary file path')

PGP_KEYS = []
for _file in os.listdir(NEW_GNUPG_HOME):
    if _file.endswith('.asc'):
        key_data = open('{}/{}'.format(NEW_GNUPG_HOME, _file)).read()
        gpg.import_keys(key_data)


engine = create_engine(DB_URI, echo=False, poolclass=NullPool, isolation_level='READ COMMITTED')
base = declarative_base()
orm_session = sessionmaker(bind=engine)
session = orm_session()


class EducationPayment(base):
    __tablename__ = 'sftp_education_payment'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    earn_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    school_id = Column(String(30), index=True)
    school_name = Column(String(255), default='School Name')
    enrolment_id = Column(INTEGER(11))
    student_id = Column(INTEGER(11))
    grade = Column(String(30))
    payment_reference_number = Column(String(50))
    payment_for = Column(String(30))
    business_category = Column(String(50), default='Education')
    charge_id = Column(String(30))
    description = Column(String(255), default='NA')
    term_number = Column(TINYINT(4), default=0)
    is_student_enrolment_this_year = Column(BIT(1), default=0)
    gross_amount = Column(Float)
    net_amount = Column(Float, default=0)
    amount_paid_by_points = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    points_redemption_reference = Column(String(50), default='NA')
    timestamp = Column(TIMESTAMP)
    csv_timestamp = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    lms_transaction_id = Column(String(255))
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class EducationEnrollmentCancellation(base):
    __tablename__ = 'sftp_education_enrollment_cancellation'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    refund_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    school_id = Column(String(30), index=True)
    school_name = Column(String(255), default='School Name')
    enrolment_id = Column(INTEGER(11))
    student_id = Column(INTEGER(11))
    payment_for = Column(String(30))
    cancellation_reference_number = Column(String(50))
    cancellation_fee = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    timestamp = Column(TIMESTAMP)
    csv_timestamp = Column(String(25))
    business_category = Column(String(50), default='Education')
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class LeasingInstalmentPayments(base):
    __tablename__ = 'sftp_leasing_instalment_payments'
    __table_args__ = {"schema": constants.ALDAR_APP}

    # TODO: installment_due_date type given datetime but value is date. Also check payment for business trigger

    id = Column(INTEGER(11), primary_key=True)
    earn_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    payment_for = Column(String(30), default='leasing_instalment_payment')        # added default payment for
    business_category = Column(String(50), default='Leasing')
    lease_contract_number = Column(String(50))
    is_renewal = Column(BIT(1), default=0)
    lease_method = Column(String(50))
    property_type = Column(String(50))
    contract_value = Column(Float)
    contract_period_in_months = Column(TINYINT(4))
    number_of_installments = Column(TINYINT(4))
    payment_reference_number = Column(String(50))
    installment_number = Column(TINYINT(4))
    installment_due_date = Column(Date)
    csv_installment_due_date = Column(String(25))
    gross_amount = Column(Float, default=0)
    net_amount = Column(Float, default=0)
    amount_paid_by_points = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    points_redemption_reference = Column(String(50), default='NA')
    payment_datetime = Column(TIMESTAMP)
    csv_payment_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    lms_transaction_id = Column(String(255))
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


# class LeasingCommunityServices(base):
#     __tablename__ = 'sftp_leasing_community_Services'
#     __table_args__ = {"schema": constants.ALDAR_APP}
#
#     id = Column(INTEGER(11), primary_key=True)
#     earn_id = Column(INTEGER(11))
#     email = Column(String(255), index=True)
#     mobile_number = Column(String(20), index=True)
#     community_id = Column(String(30), index=True)
#     community_name = Column(String(255))
#     unit_id = Column(String(50))
#     business_category = Column(String(50), default='Leasing')
#     lease_contract_number = Column(String(50))
#     payment_reference_number = Column(String(50))
#     payment_for = Column(String(50))
#     service_facility_id = Column(String(50))
#     description = Column(String(255), default='NA')
#     gross_amount = Column(Float)
#     net_amount = Column(Float)
#     amount_paid_by_points = Column(Float, default=0)
#     paid_amount = Column(Float, default=0)
#     points_redemption_reference = Column(String(50), default='NA')
#     payment_datetime = Column(TIMESTAMP)
#     csv_payment_datetime = Column(String(25))
#     status = Column(TINYINT(4), nullable=False, default=0)
#     file_name = Column(String(255), nullable=False)
#     unique_file_identifier = Column(String(255), nullable=False)
#     points = Column(Float, nullable=False, default=0)
#     lms_transaction_id = Column(String(255))
#     api_response = Column(TEXT)
#     details = Column(TEXT)
#     created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
#     updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class LeasingContractCancellations(base):
    __tablename__ = 'sftp_leasing_contract_cancellations'
    __table_args__ = {"schema": constants.ALDAR_APP}

    # TODO: lease_contract_number string in file and docs says integer

    id = Column(INTEGER(11), primary_key=True)
    refund_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    business_category = Column(String(50), default='Leasing')
    lease_contract_number = Column(String(50))
    cancellation_fee = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    cancellation_datetime = Column(TIMESTAMP)
    csv_cancellation_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class MaintenanceInstalmentPayments(base):
    __tablename__ = 'sftp_maintenance_instalment_payments'
    __table_args__ = {"schema": constants.ALDAR_APP}

    # TODO: missing document_id in file given in docs

    id = Column(INTEGER(11), primary_key=True)
    earn_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    business_category = Column(String(50), default='Maintenance')
    maintenance_contract_number = Column(String(50))
    package_type = Column(String(50))                                     # used as payment_for business trigger
    package_id = Column(String(50))
    package_detail = Column(String(255))
    contract_value = Column(Float)
    number_of_installments = Column(TINYINT(4))
    payment_reference_number = Column(String(50))
    installment_number = Column(TINYINT(4))
    property_type = Column(String(50))
    contract_period = Column(TINYINT(4), default=0)
    gross_amount = Column(Float, default=0)
    net_amount = Column(Float, default=0)
    amount_paid_by_points = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    points_redemption_reference = Column(String(50), default='NA')
    booking_datetime = Column(TIMESTAMP)
    csv_booking_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    lms_transaction_id = Column(String(255))
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class MaintenanceContractCancellations(base):
    __tablename__ = 'sftp_maintenance_contract_cancellations'
    __table_args__ = {"schema": constants.ALDAR_APP}

    # TODO: missing document_id in file given in docs

    id = Column(INTEGER(11), primary_key=True)
    refund_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    business_category = Column(String(50), default='Maintenance')
    maintenance_contract_number = Column(String(50))
    package_amount = Column(Float)
    cancellation_fee = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    cancellation_datetime = Column(TIMESTAMP)
    csv_cancellation_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class SalesInstalmentPayments(base):
    __tablename__ = 'sftp_sales_instalment_payments'
    __table_args__ = {"schema": constants.ALDAR_APP}

    # TODO: installment_due_date and order_date docs says YYYY-MM-DD but in file DD-MM-YYYY

    id = Column(INTEGER(11), primary_key=True)
    earn_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    party_id = Column(INTEGER(11))
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    payment_for = Column(String(30), default='sales_instalment_payment')
    sales_order_id = Column(INTEGER(11))
    business_category = Column(String(50), default='Sales')
    property_type = Column(String(50))
    property_gross_value = Column(Float)
    property_net_value = Column(Float)
    order_date = Column(Date)
    csv_order_date = Column(String(25))
    number_of_installments = Column(TINYINT(4))
    payment_reference_number = Column(String(50))
    installment_number = Column(TINYINT(4))
    installment_due_date = Column(Date)
    csv_installment_due_date = Column(String(25))
    is_handover = Column(BIT(1), default=0)
    gross_amount = Column(Float)
    net_amount = Column(Float)
    amount_paid_by_points = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    points_redemption_reference = Column(String(50), default='NA')
    payment_datetime = Column(TIMESTAMP)
    csv_payment_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    lms_transaction_id = Column(String(255))
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    @classmethod
    def get_records_against_sales_ids(cls, sales_order_ids):
        query = session.query(SalesInstalmentPayments).filter(
            cls.sales_order_id.in_(sales_order_ids))
        return query.all()


# class SalesCommunityServices(base):
#     __tablename__ = 'sftp_sales_community_services'
#     __table_args__ = {"schema": constants.ALDAR_APP}
#
#     # TODO: installment_due_date and order_date docs says YYYY-MM-DD but in file DD-MM-YYYY
#
#     id = Column(INTEGER(11), primary_key=True)
#     earn_id = Column(INTEGER(11))
#     email = Column(String(255), index=True)
#     mobile_number = Column(String(20), index=True)
#     party_id = Column(INTEGER(11))
#     community_id = Column(String(30), index=True)
#     community_name = Column(String(255))
#     unit_id = Column(String(50))
#     sales_order_id = Column(INTEGER(11))
#     payment_reference_number = Column(String(50))
#     payment_for = Column(String(30))
#     service_facility_id = Column(String(30))
#     description = Column(String(255), default='NA')
#     business_category = Column(String(50), default='Sales')
#     gross_amount = Column(Float)
#     net_amount = Column(Float)
#     amount_paid_by_points = Column(Float, default=0)
#     paid_amount = Column(Float, default=0)
#     points_redemption_reference = Column(String(50), default='NA')
#     payment_datetime = Column(TIMESTAMP)
#     csv_payment_datetime = Column(String(25))
#     status = Column(TINYINT(4), nullable=False, default=0)
#     file_name = Column(String(255), nullable=False)
#     unique_file_identifier = Column(String(255), nullable=False)
#     points = Column(Float, nullable=False, default=0)
#     lms_transaction_id = Column(String(255))
#     api_response = Column(TEXT)
#     details = Column(TEXT)
#     created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
#     updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class SalesContractCancellations(base):
    __tablename__ = 'sftp_sales_contract_cancellations'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    refund_id = Column(INTEGER(11))
    email = Column(String(255), index=True)
    mobile_number = Column(String(20), index=True)
    party_id = Column(INTEGER(11))
    community_id = Column(String(30), index=True)
    community_name = Column(String(255))
    unit_id = Column(String(50))
    sales_order_id = Column(INTEGER(11))
    business_category = Column(String(50), default='Sales')
    cancellation_fee = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    cancellation_datetime = Column(TIMESTAMP)
    csv_cancellation_datetime = Column(String(25))
    status = Column(TINYINT(4), nullable=False, default=0)
    file_name = Column(String(255), nullable=False)
    unique_file_identifier = Column(String(255), nullable=False)
    points = Column(Float, nullable=False, default=0)
    api_response = Column(TEXT)
    details = Column(TEXT)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


MODEL_CLASSES = dict(
    EducationPayment=EducationPayment,
    EducationEnrollmentCancellation=EducationEnrollmentCancellation,
    LeasingInstalmentPayments=LeasingInstalmentPayments,
    # LeasingCommunityServices=LeasingCommunityServices,
    LeasingContractCancellations=LeasingContractCancellations,
    MaintenanceInstalmentPayments=MaintenanceInstalmentPayments,
    MaintenanceContractCancellations=MaintenanceContractCancellations,
    SalesInstalmentPayments=SalesInstalmentPayments,
    # SalesCommunityServices=SalesCommunityServices,
    SalesContractCancellations=SalesContractCancellations
)


class SftpFileStatus(base):
    __tablename__ = 'sftp_file_status'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    directory = Column(String(30))
    file_name = Column(String(255), nullable=False)
    status = Column(TINYINT(4), nullable=False, default=0)
    details = Column(TEXT)
    total_records = Column(INTEGER(11))
    valid_transactions = Column(INTEGER(11))
    date_created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)


class SftpDirectoryConfiguration(base):
    __tablename__ = 'sftp_directory_configuration'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    date_created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    date_last_updated = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    asset = Column(String(30))
    directory_name = Column(String(30))
    logging_enabled = Column(BIT(1), default=0)
    email_notification_enabled = Column(BIT(1), default=0)
    email_recipients = Column(String(255))
    log_encryption_key = Column(String(255))
    comments = Column(String(100))

    @classmethod
    def get_sftp_configuration(cls, directory_name):
        """
        Returns sftp directory info against directory
        :param str directory_name: name of directory
        :rtype: SftpDirectoryConfiguration
        """
        return session.query(SftpDirectoryConfiguration).filter(cls.directory_name == directory_name).one()


class ConceptIdMapping(base):
    __tablename__ = 'concept_id_mapping'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    date_created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    date_updated = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    asset = Column(String(30), nullable=False)
    aldar_concept_id = Column(String(50), nullable=False)
    aldar_concept_name = Column(String(100), nullable=False)
    lms_concept_id = Column(String(50), nullable=False)
    lms_concept_name = Column(String(100), nullable=False)
    comments = Column(String(100))

    @classmethod
    def get_concept_id_mappings_by_asset(cls, asset_name):
        """
        Returns lms concept id mappings against asset
        :param str asset_name: name of asset
        :rtype: list
        """
        return session.query(ConceptIdMapping).filter(cls.asset == asset_name).all()


class Earn(base):
    __tablename__ = 'earn'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    date_created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    date_last_updated = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    source = Column(String(50), default='SFTP', index=True, nullable=False)
    user_id = Column(INTEGER(11), index=True, nullable=False)
    business_category = Column(String(50))
    business_trigger = Column(String(30))
    concept_id = Column(String(30), index=True)
    concept_name = Column(String(255))
    external_transaction_id = Column(String(255), nullable=False, index=True)
    gross_total_amount = Column(Float)
    net_amount = Column(Float)
    amount_paid_using_points = Column(Float)
    paid_amount = Column(Float)
    redemption_reference = Column(String(50))
    currency = Column(String(50))
    charge_id = Column(String(30))
    description = Column(TEXT)
    transaction_datetime = Column(TIMESTAMP)
    lms_earn_transaction_id = Column(String(255))
    points_earned = Column(Float)
    earn_rate = Column(Float)
    bonus_points = Column(Float)
    referrer_bonus_points = Column(Float)
    member_tier = Column(String(50))
    tier_updated = Column(BIT(1))


class Refund(base):
    __tablename__ = 'refund'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    date_created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    date_last_updated = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    source = Column(String(50), default='SFTP', index=True, nullable=False)
    user_id = Column(INTEGER(11), index=True, nullable=False)
    business_category = Column(String(50))
    business_trigger = Column(String(30))
    concept_id = Column(String(30), index=True)
    concept_name = Column(String(255))
    transaction_id = Column(String(255), nullable=False, index=True)
    refund_points_mode = Column(String(255), nullable=False)
    refund_amount = Column(Float)
    property_net_value = Column(Float)
    response_value = Column(Float)
    currency = Column(String(50))
    description = Column(TEXT)
    points_refunded = Column(Float)
    points_balance = Column(Float)


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
    membership_id = Column(String(20), nullable=True)
    enable_email_notification = Column(TINYINT, default=1)
    enable_push_notification = Column(TINYINT, default=1)

    @classmethod
    def get_lms_user_by_email(cls, email):
        """
        Returns user against email and also if lms_membership_id exists
        :param str email: email
        :rtype: User
        """
        return session.query(User).filter(cls.email == email, cls.lms_membership_id != None).first()


class WlUserGroup(base):
    __tablename__ = 'wl_user_group'
    __table_args__ = {"schema": constants.ENTERTAINER_WEB}

    # Columns
    id = Column(INTEGER(11), primary_key=True)
    wl_company = Column(String(45))
    user_group = Column(INTEGER(11))
    name = Column(String(45))
    code = Column(String(5))
    logo = Column(String(250))
    number_of_offers = Column(INTEGER(11), default=0)
    expiration_date = Column(Date)
    hierarchy = Column(INTEGER(11), default=0)
    keys_expire_in_days = Column(INTEGER(11), default=0)
    is_primary_group = Column(TINYINT(1), default=1)

    @classmethod
    def get_by_name(cls, name):
        """
        get user_group info by name and company

        :param str name: Name of group
        :rtype: group information or None
        """
        return session.query(WlUserGroup).filter(cls.name == name, cls.wl_company == constants.ADR).first()


class Wlvalidation(base):
    __tablename__ = 'wlvalidation'
    __table_args__ = {"schema": constants.ENTERTAINER_WEB}

    # Columns
    id = Column(INTEGER(11), primary_key=True)
    wl_key = Column(String(24), nullable=False)
    wl_company = Column(String(5), nullable=False)
    email = Column(String(255), nullable=False)
    isused = Column(BIT(1), nullable=False)
    customer_id = Column(INTEGER(11), index=True)
    activation_date = Column(DateTime)
    active = Column(BIT(1), nullable=False)
    is_expired = Column(BIT(1), index=True)
    existing = Column(BIT(1), nullable=False, default=True)
    user_group = Column(TINYINT(1), default=1)
    expiry_date = Column(DateTime)
    deactivation_date = Column(DateTime)
    comments = Column(String(50))
    date_created = Column(TIMESTAMP, default=datetime.datetime.now)
    date_updated = Column(TIMESTAMP, default=datetime.datetime.now)

    @classmethod
    def get_user_groups(cls, company, user_id):
        """
        Gets the user Groups
        :param str company: Company
        :param int user_id: User ID
        :rtype: list
        """
        results = session.query(Wlvalidation).with_entities(
            cls.user_group,
            func.count(cls.user_group).label('quantity')
        ).filter(
            cls.customer_id == user_id,
            cls.wl_company == company,
            cls.active == 1
        ).group_by(cls.user_group).all()
        user_groups = []
        for result in results:
            user_groups.extend(repeat(result[0], result[1]))
        return user_groups

    @classmethod
    def deactivate_previous_user_groups(cls, company, user_id, user_current_group_id):
        changes = {'active': 0}
        session.query(Wlvalidation).filter(
            cls.wl_company == company,
            cls.customer_id == user_id,
            cls.id != user_current_group_id
        ).update(changes)
        session.commit()


class LMSConceptIds(base):
    __tablename__ = 'lms_concept_ids'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    asset = Column(String(50), nullable=False)
    concept_id = Column(String(50), nullable=False)
    concept_name = Column(String(100), nullable=False)

    @classmethod
    def get_concept_ids_by_asset(cls, asset_name):
        query = session.query(LMSConceptIds).with_entities(
            LMSConceptIds.concept_id
        ).filter(cls.asset == asset_name)
        return query.all()


class MerchantMapping(base):
    __tablename__ = 'merchant_mapping'
    __table_args__ = {"schema": constants.ENTERTAINER_WEB}

    id = Column(INTEGER(11), primary_key=True)
    et_merchant_id = Column(INTEGER(11), index=True)
    category = Column(String(50), index=True)
    sub_category = Column(String(50), index=True)
    sub_category_l2 = Column(String(50), index=True)
    location_id = Column(INTEGER(11), index=True, default=0)
    is_active = Column(TINYINT(1), index=True, default=1)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP)


class Outlet(base):
    __tablename__ = 'outlet'
    __table_args__ = {"schema": constants.ENTERTAINER_WEB}

    id = Column(INTEGER(11), primary_key=True)
    sf_id = Column(String(20), unique=True, comment='Salesforce ID. OXXXXXX')
    merchant_id = Column(INTEGER(11), nullable=False, index=True)
    location_id = Column(INTEGER(11), index=True)
    product_location = Column(String(100))
    lat = Column(Float(10))
    lng = Column(Float(10))
    email = Column(String(255))
    telephone = Column(String(45))
    fax = Column(String(45))
    delivery_telephone = Column(String(45))
    active = Column(TINYINT(1), nullable=False, index=True, default=0)
    billing_country = Column(String(45), index=True)
    area_group = Column(String(255))
    ta_location_id = Column(INTEGER(10))
    ta_rating = Column(Float(6))
    ta_reviews_count = Column(INTEGER(11))
    ta_rating_img_url = Column(String(255))
    redemption_emails = Column(String(500))
    amz_update_time = Column(TIMESTAMP)
    billing_city = Column(String(250))
    sf_account_id = Column(String(50))
    merlin_url = Column(String(500))
    integration_type = Column(String(100))
    integration_type_other = Column(String(255))
    min_order_amount = Column(Float(10))
    del_charge_total = Column(Float(10))
    del_charge_min = Column(Float(10))
    min_order_cap = Column(BIT(1))
    del_charge_on_total_order = Column(BIT(1))
    del_charge_on_less_than_min = Column(BIT(1))
    cinema_venue_id = Column(INTEGER(11))
    table_reservation_enabled = Column(BIT(1), index=True)
    table_reservation_email = Column(String(550))
    invoice_entity_id = Column(String(100))
    invoice_entity_name = Column(String(100))
    external_id = Column('af_external_id', String(50), index=True)
    concept_id = Column(String(30), nullable=True)

    @classmethod
    def get_concept_ids_by_asset(cls, asset_name):
        query = session.query(Outlet).join(
            MerchantMapping,
            Outlet.merchant_id == MerchantMapping.et_merchant_id
        ).with_entities(
            Outlet.concept_id
        ).filter(MerchantMapping.category == asset_name)
        return query.all()


class MaintenancePackagesLookUp(base):
    __tablename__ = 'maintenance_packages_lookup'
    __table_args__ = {"schema": constants.ALDAR_APP}

    id = Column(INTEGER(11), primary_key=True)
    service_id = Column(String(50), nullable=False)
    description = Column(String(255), default='NA')

    @classmethod
    def get_package_ids(cls):
        query = session.query(MaintenancePackagesLookUp).with_entities(MaintenancePackagesLookUp.service_id)
        return query.all()


class Session(base):
    __tablename__ = 'session'
    __table_args__ = {'schema': constants.ENTERTAINER_WEB}

    id = Column(INTEGER(11), primary_key=True)
    session_token = Column(String(100))
    customer_id = Column(INTEGER(10), nullable=False)
    member_type = Column(TINYINT(1))
    primary_user_id = Column(INTEGER(11))
    family_id = Column(INTEGER(11))
    include_cheers = Column(BIT(1))
    data = Column(String(5120))
    date_cached = Column(INTEGER(10))
    date_created = Column(TIMESTAMP, default=datetime.datetime.now)
    last_activity_date = Column(TIMESTAMP, default=datetime.datetime.now)
    refresh_required = Column(BIT(1))
    guest_email = Column(String(255))
    guest_nickname = Column(String(255))
    guest_relationship = Column(String(255))
    isactive = Column(BIT(1), nullable=False, default=1)
    company = Column(String(20), default='entertainer')
    isagreed = Column(BIT(1))
    date_agreed = Column(DateTime)
    ping_offer_limit = Column(INTEGER(10), default=10)
    app_version = Column(String(255))
    product_ids = Column(String(2500))
    extended_trail_group_ids = Column(String(300))

    @classmethod
    def update_all_sessions_for_customer(cls, customer_id, company):
        """
        Updates all the sessions of the customer on the base of the company and id
        :param int customer_id: id of customer
        :param str company: company of the customer
        """
        date_cached = time.time()
        changes = {'date_cached': date_cached, 'refresh_required': 1}
        session.query(Session).filter(cls.company == company, cls.customer_id == customer_id).update(changes)
        session.commit()


class EntSendEmail(base):
    __tablename__ = 'ent_send_emails'
    __table_args__ = {"schema": constants.CONSOLIDATION}

    PRIORITY_HIGH = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_LOW = 3

    id = Column(INTEGER(11), primary_key=True)
    email_to = Column(String(255))
    email_template_type_id = Column(INTEGER(11))
    email_template_data = Column(String(500))
    optional_data = Column(TEXT, nullable=False)
    language = Column(String(5))
    priority = Column(INTEGER(5))
    created_date = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    is_sent = Column(TINYINT(1), default=0)


class AldarCSVDataSync(object):

    def __init__(self, sftp_client, aldar_business_trigger_dir, business_trigger_data):
        self.sftp_client = sftp_client
        self.aldar_business_trigger_dir_name = aldar_business_trigger_dir
        self.aldar_business_trigger_data = business_trigger_data
        self.aldar_business_trigger_remote_path = '{}/{}'.format(sftp_client.pwd, aldar_business_trigger_dir)
        self.aldar_business_trigger_local_path = '{}/{}'.format(LOCAL_FILE_DIR, aldar_business_trigger_dir)
        self.validation_schema = business_trigger_data.get('schema_class')
        self.db_model_class = MODEL_CLASSES.get(business_trigger_data.get('model_class'))
        self.asset = business_trigger_data.get('asset')
        self.unique_file_identifier = None
        self.aldar_business_trigger_dir_config = SftpDirectoryConfiguration.get_sftp_configuration(
            aldar_business_trigger_dir
        )
        self.total_records_in_file = None
        self.successfully_processed_records = 0

    def validate_directory(self, path):
        if self.sftp_client.isdir(path):
            return True
        return False

    def log_file_status(self, file_name, detail, status=0):
        try:
            file_status = SftpFileStatus(
                directory=self.aldar_business_trigger_dir_name,
                file_name=file_name,
                status=status,
                details=detail,
                total_records=self.total_records_in_file,
                valid_transactions=self.successfully_processed_records
            )
            session.add(file_status)
            session.commit()
            self.notify_file_status_via_emails(file_name, status, detail)
        except Exception as error:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in saving file status. File name {file_name} \n "
                "Error Details are {error_details}".format(
                    file_name=file_name,
                    error_details=error
                )
            )

    def notify_file_status_via_emails(self, file_name, status, detail):
        if (
                self.aldar_business_trigger_dir_config.email_notification_enabled and
                self.aldar_business_trigger_dir_config.email_recipients
        ):
            email_recipients = self.aldar_business_trigger_dir_config.email_recipients.split(';')
            email_data = {"{FILE_NAME}": '{} - {}'.format(self.aldar_business_trigger_dir_name, file_name)}
            template_id = ALDAR_SFTP_SUCCESS_TEMPLATE_ID
            if not status:
                template_id = ALDAR_SFTP_FAILURE_TEMPLATE_ID
                email_data["{ERROR_DETAIL}"] = detail

            for email in email_recipients:
                try:
                    ent_send_email = EntSendEmail(
                        email_template_type_id=template_id,
                        email_template_data='',
                        email_to=email,
                        language='en',
                        priority=EntSendEmail.PRIORITY_HIGH,
                        created_date=datetime.datetime.now(),
                        optional_data=php_json_dumps(email_data).decode(errors='ignore')
                    )
                    session.add(ent_send_email)
                    session.commit()
                except Exception as error:
                    session.rollback()
                    ERROR_LOGGER.exception(
                        "exception occurred in adding entry for file status in EntSendEmail. File name "
                        "{file_name} \n Error Details are {error_details}".format(
                            file_name=file_name,
                            error_details=error
                        )
                    )

    def validate_file_not_exist_in_archive_directory(self, _file_name):
        archive_file_path = '{}/archive/{}'.format(self.aldar_business_trigger_remote_path, _file_name)
        if self.sftp_client.exists(archive_file_path):
            self.log_file_status(
                _file_name,
                'Duplicate File. \nFile with this name already exist in archive directory. File name = {}'.format(
                    _file_name
                )
            )
            self.handle_error_file(_file_name)
            return True
        return False

    def decrypt_file(self, _file_name):
        output_file = ''
        try:
            with open('{}/{}'.format(self.aldar_business_trigger_local_path, _file_name), 'rb') as f:
                decrypted_file_name = 'decryted_{}'.format(_file_name)
                _output_file = '{}/{}'.format(self.aldar_business_trigger_local_path, decrypted_file_name)
                status = gpg.decrypt_file(f, passphrase=ENTERTAINER_PASS_PHRASE, output=_output_file)
                if status.ok and status.status == 'decryption ok':
                    output_file = decrypted_file_name
                else:
                    ERROR_LOGGER.exception(
                        "Aldar encrypted file can't be decrypted. File name = {_file_name}\n decryption_status = "
                        "{status}\n decryption_error = {error}".format(
                            _file_name=_file_name,
                            status=status.status,
                            error=status.stderr
                        )
                    )
                    self.handle_error_file(_file_name)
                    self.log_file_status(_file_name, 'Unable to decrypt file.')
        except Exception as error:
            ERROR_LOGGER.exception(
                "Exception occurred in decrypting file. File name {_file_name} \n "
                "Error Details are {error_details}".format(
                    _file_name=_file_name,
                    error_details=error
                )
            )
            self.log_file_status(
                _file_name,
                'Exception occurred in decrypting file. \nError detail {}'.format(error.args)
            )
            self.handle_error_file(_file_name)
        return output_file

    def get_csv_list(self, _dir):
        """
        Download files from remote directory to local directory and returns file names
        :param str _dir: Directory Path
        """
        csv_files = []
        self.sftp_client.get_d(_dir, self.aldar_business_trigger_local_path)

        for file_name in os.listdir(self.aldar_business_trigger_local_path):
            csv_files.append(file_name)
        return csv_files

    def does_file_exists(self, remote_file_path, csv_file_name):
        if self.sftp_client.exists(remote_file_path):
            self.sftp_client.remove(remote_file_path)

    def handle_error_file(self, csv_file_name):
        upload_remote_file_path = '{}/upload/{}'.format(self.aldar_business_trigger_remote_path, csv_file_name)
        error_remote_file_path = '{}/error/{}'.format(self.aldar_business_trigger_remote_path, csv_file_name)
        self.does_file_exists(error_remote_file_path, csv_file_name)
        self.sftp_client.rename(upload_remote_file_path, error_remote_file_path)

    def process_csv(self, csv_file_name, remote_file_name):
        valid_records = []
        invalid_records = []
        try:
            with open('{}/{}'.format(self.aldar_business_trigger_local_path, csv_file_name), encoding='utf-8', mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                csv_reader.fieldnames = [name.lower() for name in csv_reader.fieldnames]
                if set(csv_reader.fieldnames) == set(self.aldar_business_trigger_data['csv_header']):
                    self.unique_file_identifier = str(datetime.datetime.now().timestamp())
                    for row in csv_reader:
                        try:
                            row['unique_file_identifier'] = self.unique_file_identifier
                            row['file_name'] = remote_file_name
                            sanitized_row = self.validation_schema().load(row)
                            valid_records.append(self.db_model_class(**sanitized_row))
                        except ValidationError as e:
                            ERROR_LOGGER.exception("Faulty record detected: {}, {}".format(row, e))
                            for key, error in e.messages.items():
                                e.valid_data[key] = None
                            e.valid_data['details'] = json.dumps(e.messages)
                            e.valid_data['status'] = constants.STATUS_ERROR
                            invalid_records.append(self.db_model_class(**e.valid_data))
                else:
                    ERROR_LOGGER.exception(
                        "exception occurred in reading file i.e incorrect header. Aldar user directory "
                        "{aldar_dir} \n file_name = {file_name}\nFile header is {header}".format(
                            aldar_dir=self.aldar_business_trigger_dir_name,
                            file_name=remote_file_name,
                            header=csv_reader.fieldnames
                        )
                    )
                    self.log_file_status(
                        remote_file_name,
                        "File Header doesn't match. \nError detail {}".format(
                            set(csv_reader.fieldnames) - set(self.aldar_business_trigger_data['csv_header'])
                        )
                    )
                    self.handle_error_file(remote_file_name)
                    return False
        except Exception as error:
            ERROR_LOGGER.exception(
                "exception occurred in reading file. Aldar user directory {aldar_dir} \n "
                "file_name = {file_name}\nError Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    file_name=remote_file_name,
                    error_details=error
                )
            )
            self.log_file_status(remote_file_name, 'Unable to process File. \nError detail {}'.format(error.args))
            self.handle_error_file(remote_file_name)
            return False

        self.total_records_in_file = len(valid_records) + len(invalid_records)

        if self.total_records_in_file > 5000:
            self.log_file_status(
                remote_file_name,
                'Unable to process the file. Number of records should be less than 5000.'
            )
            self.handle_error_file(remote_file_name)
            return False

        try:
            if valid_records:
                session.add_all(valid_records)
                session.commit()
        except Exception as err:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in saving file records in database. Aldar user directory {aldar_dir} \n "
                "Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    error_details=err
                )
            )

        try:
            if invalid_records:
                session.add_all(invalid_records)
                session.commit()
        except Exception as err:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in saving file invalid records in database. Aldar user directory {aldar_dir} "
                "\n Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    error_details=err
                )
            )

        return True

    def get_csv_file_records(self, csv_file_name, all_records=False, page=0, page_size=None):
        query = session.query(self.db_model_class).filter(
            self.db_model_class.file_name == csv_file_name,
            self.db_model_class.unique_file_identifier == self.unique_file_identifier
        )
        if not all_records:
            query = query.filter(self.db_model_class.status == constants.STATUS_PENDING)
        if page_size:
            query = query.limit(page_size)
        if page:
            query = query.offset(page * page_size)

        return query.all()

    def get_valid_concept_ids(self):
        records = []
        for rec in Outlet.get_concept_ids_by_asset(self.asset):
            if rec.concept_id:
                records.append(rec.concept_id)
        return records

    def get_concept_id_mappings(self):
        records = {}
        for rec in ConceptIdMapping.get_concept_id_mappings_by_asset(self.asset):
            if rec.aldar_concept_id and rec.lms_concept_id:
                records[rec.aldar_concept_id] = rec.lms_concept_id
        return records

    def get_valid_package_ids(self):
        records = []
        for rec in MaintenancePackagesLookUp.get_package_ids():
            records.append(rec.service_id)
        return records

    def get_records_against_sales_ids(self, sales_order_ids):
        records = {}
        for rec in SalesInstalmentPayments.get_records_against_sales_ids(sales_order_ids):
            records[rec.sales_order_id] = rec
        return records

    def validate_records(self, csv_records):
        records = []
        update_records = []
        concept_ids = self.get_valid_concept_ids()
        concept_id_mappings = self.get_concept_id_mappings()
        for record in csv_records:
            user = User.get_lms_user_by_email(record.email)
            if user:
                data = self.validation_schema().dump(record)
                if data['concept_id'] in concept_id_mappings:
                    data['concept_id'] = concept_id_mappings[data['concept_id']]
                if data['concept_id'] in concept_ids:
                    data['member_id'] = user.lms_membership_id
                    data['user_id'] = user.id
                    records.append(data)
                else:
                    update_records.append({
                        'status': constants.STATUS_ERROR,
                        'details': "Invalid concept id",
                        'updated_at': datetime.datetime.now(),
                        'id': record.id
                    })
            else:
                update_records.append({
                    'status': constants.STATUS_ERROR,
                    'details': "Member/email doesn't exist in Entertainer",
                    'updated_at': datetime.datetime.now(),
                    'id': record.id
                })

        if self.aldar_business_trigger_data.get('model_class') == 'MaintenanceInstalmentPayments':
            package_ids = self.get_valid_package_ids()
            maintenance_valid_records = []
            for data in records:
                if data['package_id'] not in package_ids:
                    update_records.append({
                        'status': constants.STATUS_ERROR,
                        'details': "Package doesn't exist in Entertainer Maintenance look up.",
                        'updated_at': datetime.datetime.now(),
                        'id': data['id']
                    })
                else:
                    maintenance_valid_records.append(data)
            records = maintenance_valid_records

        if update_records:
            session.bulk_update_mappings(self.db_model_class, update_records)
            session.commit()
        return records

    def update_user_tier_information(self, user_email, tier_name):
        current_user_group = WlUserGroup.get_by_name(tier_name)
        if current_user_group:
            user = User.get_lms_user_by_email(user_email)
            if user:
                user_groups = Wlvalidation.get_user_groups(company=constants.ADR, user_id=user.et_user_id)
                if current_user_group.user_group not in user_groups:
                    bind_group = Wlvalidation(
                        wl_company=constants.ADR,
                        wl_key="{}{}".format(constants.ADR, randint(100000, 999999)),
                        email=user_email,
                        customer_id=user.et_user_id,
                        isused=1,
                        active=1,
                        user_group=current_user_group.user_group,
                        activation_date=datetime.datetime.now()
                    )
                    session.add(bind_group)
                    session.commit()
                    # deactivate previous active user_group
                    Wlvalidation.deactivate_previous_user_groups(constants.ADR, user.et_user_id, bind_group.id)

                    # refresh session token
                    Session.update_all_sessions_for_customer(user.et_user_id, constants.ADR)

    def process_lms_earn_api(self, csv_file_name):
        records = self.get_csv_file_records(csv_file_name)
        records = self.validate_records(records)
        total_chunks_count = ceil(len(records) / CHUNK_SIZE)
        update_records = []

        lms_manager = LMSManager(
            LMS_GRANT_TYPE,
            SFTP_USERS.get(self.aldar_business_trigger_dir_name).get('user_name'),
            SFTP_USERS.get(self.aldar_business_trigger_dir_name).get('password'),
            LMS_BASIC_AUTH,
            LMS_AUTH_URL
        )
        for offset in range(total_chunks_count):
            api_data = records[offset * CHUNK_SIZE: (offset + 1) * CHUNK_SIZE]
            response = lms_manager.earn(api_data, LMS_EARN_POINTS_URL)
            update_record_data = dict()
            if isinstance(response, dict) and response.get('batch_earn', {}):
                for res in response.get('batch_earn', {}).get('failed', []):
                    update_record_data.update(status=constants.STATUS_ERROR, details=res.get('message', ''))
                for res in response.get('batch_earn', {}).get('success', []):
                    if res.get('tier_updated'):
                        self.update_user_tier_information(res.get('email'), res.get('member_tier'))
                    earn_id = self.process_centralized_logging_for_earn(api_data[0], res)
                    update_record_data.update(
                        status=constants.STATUS_PROCESSED,
                        details='Processed successfully',
                        lms_transaction_id=res.get('earn_transaction_id', ''),
                        points=res.get('earned_points', 0),
                        earn_id=earn_id
                    )
                    self.successfully_processed_records += 1
                if 'failed' not in response.get('batch_earn', {}) and 'success' not in response.get('batch_earn', {}):
                    update_record_data.update(
                        status=constants.STATUS_ERROR,
                        details='LMS api has sent an unhandled response',
                    )
            else:
                update_record_data.update(
                    status=constants.STATUS_ERROR,
                    details='LMS api returned an unexpected response.'
                )
            update_record_data.update(
                id=api_data[0].get('id', 0),
                updated_at=datetime.datetime.now(),
                api_response=json.dumps(response)
            )
            update_records.append(update_record_data)
            time.sleep(DELAY_BETWEEN_LMS_API_REQUESTS)
        if update_records:
            session.bulk_update_mappings(self.db_model_class, update_records)
            session.commit()

    def process_centralized_logging_for_earn(self, earn_record, earn_response):
        try:
            earn_obj = Earn(
                user_id=earn_record.get('user_id'),
                business_category=earn_record.get('business_category'),
                business_trigger=earn_record.get('business_trigger'),
                concept_id=earn_record.get('concept_id'),
                concept_name=earn_record.get('concept_name'),
                external_transaction_id=earn_record.get('external_transaction_id'),
                gross_total_amount=earn_record.get('gross_total_amount'),
                net_amount=earn_record.get('net_amount'),
                amount_paid_using_points=earn_record.get('amount_paid_using_points'),
                paid_amount=earn_record.get('paid_amount'),
                redemption_reference=earn_record.get('redemption_reference'),
                currency=earn_record.get('currency'),
                charge_id=earn_record.get('charge_id'),
                description=earn_record.get('description'),
                transaction_datetime=earn_record.get('transaction_datetime'),
                lms_earn_transaction_id=earn_response.get('earn_transaction_id'),
                points_earned=earn_response.get('earned_points'),
                earn_rate=earn_response.get('earn_rate'),
                bonus_points=earn_response.get('bonus_points'),
                member_tier=earn_response.get('member_tier'),
                tier_updated=earn_response.get('tier_updated'),
                referrer_bonus_points=earn_response.get('referrer_bonus_points', []) if earn_response.get(
                    'referrer_bonus_points', []
                ) else 0
            )
            session.add(earn_obj)
            session.commit()
            return earn_obj.id
        except Exception as error:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in logging record in centralized earn table. "
                "Aldar user directory {aldar_dir} \n earn record id = {earn_record_id} \n"
                "Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    earn_record_id=earn_record.get('id'),
                    error_details=error
                )
            )

    def validate_records_for_refund(self, records):
        update_records = []
        if self.aldar_business_trigger_data.get('model_class') == 'SalesContractCancellations':
            sales_order_ids = []
            for record in records:
                sales_order_ids.append(record.get('sales_order_id'))
            if sales_order_ids:
                valid_sales_order_ids = self.get_records_against_sales_ids(sales_order_ids)
                sales_valid_records = []
                for data in records:
                    if data['sales_order_id'] not in valid_sales_order_ids.keys():
                        update_records.append({
                            'status': constants.STATUS_ERROR,
                            'details': "Sales_order_id doesn't exist in Entertainer Sales Instalment Payments records.",
                            'updated_at': datetime.datetime.now(),
                            'id': data['id']
                        })
                    else:
                        rec = valid_sales_order_ids[data['sales_order_id']]
                        data['property_net_value'] = rec.property_net_value
                        sales_valid_records.append(data)
                records = sales_valid_records

        if update_records:
            session.bulk_update_mappings(self.db_model_class, update_records)
            session.commit()

        return records

    def process_lms_refund_api(self, csv_file_name):
        records = self.get_csv_file_records(csv_file_name)
        records = self.validate_records(records)
        records = self.validate_records_for_refund(records)
        update_records = []
        lms_manager = LMSManager(
            LMS_GRANT_TYPE,
            SFTP_USERS.get(self.aldar_business_trigger_dir_name).get('user_name'),
            SFTP_USERS.get(self.aldar_business_trigger_dir_name).get('password'),
            LMS_BASIC_AUTH,
            LMS_AUTH_URL
        )
        for record in records:
            response = lms_manager.refund(record, LMS_REFUND_POINTS_URL)
            update_record_data = dict()
            if isinstance(response, dict):
                if 'errors' in response and response.get('errors', []):
                    errors = response.get('errors', [])[0]
                    update_record_data.update(status=constants.STATUS_ERROR, details=json.dumps(errors))
                elif 'refund' in response:
                    refund_id = self.process_centralized_logging_for_refund(record, response.get('refund', {}))
                    update_record_data.update(
                        status=constants.STATUS_PROCESSED,
                        details='Processed successfully',
                        points=response.get('refund', {}).get('points', 0),
                        refund_id=refund_id
                    )
                    self.successfully_processed_records += 1
                else:
                    update_record_data.update(
                        status=constants.STATUS_ERROR,
                        details='LMS api has sent an unhandled response',
                    )
            else:
                update_record_data.update(
                    status=constants.STATUS_ERROR,
                    details='LMS api returned an unexpected response.'
                )
            update_record_data.update(
                id=record.get('id', 0),
                updated_at=datetime.datetime.now(),
                api_response=json.dumps(response)
            )
            update_records.append(update_record_data)
            time.sleep(DELAY_BETWEEN_LMS_API_REQUESTS)
        if update_records:
            session.bulk_update_mappings(self.db_model_class, update_records)
            session.commit()

    def process_centralized_logging_for_refund(self, cancellation_record, refund_response):
        try:
            refund_obj = Refund(
                user_id=cancellation_record.get('user_id'),
                business_category=cancellation_record.get('business_category'),
                business_trigger=cancellation_record.get('business_trigger'),
                concept_id=cancellation_record.get('concept_id'),
                concept_name=cancellation_record.get('concept_name'),
                transaction_id=cancellation_record.get('transaction_id'),
                refund_points_mode=cancellation_record.get('refund_points_mode'),
                refund_amount=cancellation_record.get('refund_amount'),
                property_net_value=cancellation_record.get('property_net_value'),
                response_value=refund_response.get('value'),
                currency=cancellation_record.get('currency'),
                description=cancellation_record.get('description'),
                points_refunded=refund_response.get('points'),
                points_balance=refund_response.get('points_balance')
            )
            session.add(refund_obj)
            session.commit()
            return refund_obj.id
        except Exception as error:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in logging record in centralized refund table. "
                "Aldar user directory {aldar_dir} \n cancellation record id = {cancellation_record_id} \n"
                "Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    cancellation_record_id=cancellation_record.get('id'),
                    error_details=error
                )
            )

    def write_csv(self, csv_file_name, rows):
        log_file_name = 'unencrypted_log_{}'.format(csv_file_name)
        local_log_file_path = os.path.join(self.aldar_business_trigger_local_path, log_file_name)
        header_row = self.aldar_business_trigger_data['csv_header'].copy()
        header_row.extend(['status', 'points', 'message'])
        with open(local_log_file_path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=header_row, extrasaction='ignore', delimiter=',')
            writer.writeheader()
            for row in rows:
                row = row.__dict__
                row['message'] = row['details']
                for log_file_date_key in self.aldar_business_trigger_data['log_file_date_keys']:
                    row[log_file_date_key['update_key']] = row[log_file_date_key['from_key']]
                writer.writerow(row)
        with open(local_log_file_path, 'rb') as f:
            encrypted_log_file_path = os.path.join(self.aldar_business_trigger_local_path, 'log_{}'.format(csv_file_name))
            status = gpg.encrypt_file(
                f,
                recipients=[self.aldar_business_trigger_dir_config.log_encryption_key],
                output=encrypted_log_file_path,
                always_trust=True
            )
        remote_log_file_path = os.path.join(self.aldar_business_trigger_remote_path, 'logs', 'log_{}'.format(csv_file_name))
        self.does_file_exists(remote_log_file_path, 'log_{}'.format(csv_file_name))
        self.sftp_client.put(encrypted_log_file_path, remote_log_file_path)

    def move_file_to_archive(self, csv_file_name):
        upload_remote_file_path = '{}/upload/{}'.format(self.aldar_business_trigger_remote_path, csv_file_name)
        archive_remote_file_path = '{}/archive/{}'.format(self.aldar_business_trigger_remote_path, csv_file_name)
        self.sftp_client.rename(upload_remote_file_path, archive_remote_file_path)

    def create_log_file(self, csv_file_name):
        csv_records = self.get_csv_file_records(csv_file_name, all_records=True)
        if csv_records:
            self.write_csv(csv_file_name, csv_records)
        self.log_file_status(csv_file_name, 'Processed Successfully.', 1)

    def sync_aldar_sftp_transaction_sync(self):
        try:
            results = session.execute('call aldar_app.aldar_sftp_transaction_sync(:asset_type)', {'asset_type': self.asset})
            session.commit()
        except Exception as error:
            session.rollback()
            ERROR_LOGGER.exception(
                "exception occurred in running store procedure. Aldar user directory {aldar_dir} \n "
                "Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    error_details=error
                )
            )

    def run(self):
        try:
            if not self.validate_directory('{}/{}'.format(self.aldar_business_trigger_remote_path, 'upload')):
                raise Exception("Invalid upload_DIR")
            if not self.validate_directory('{}/{}'.format(self.aldar_business_trigger_remote_path, 'archive')):
                raise Exception("Invalid archive_DIR")
            if not self.validate_directory('{}/{}'.format(self.aldar_business_trigger_remote_path, 'error')):
                raise Exception("Invalid error_DIR")
            if not self.validate_directory('{}/{}'.format(self.aldar_business_trigger_remote_path, 'logs')):
                raise Exception("Invalid logs_DIR")

            csv_lists = self.get_csv_list('{}/{}'.format(self.aldar_business_trigger_remote_path, 'upload'))
            for _csv in csv_lists:
                self.total_records_in_file = None
                self.successfully_processed_records = 0
                if self.validate_file_not_exist_in_archive_directory(_csv):
                    continue
                decrypted_csv_file = self.decrypt_file(_csv)
                if not decrypted_csv_file:
                    continue
                csv_processed = self.process_csv(decrypted_csv_file, _csv)
                if csv_processed:
                    if self.aldar_business_trigger_data.get('refund_api'):
                        self.process_lms_refund_api(_csv)
                    else:
                        self.process_lms_earn_api(_csv)
                    self.move_file_to_archive(_csv)
                    self.create_log_file(_csv)
                    self.sync_aldar_sftp_transaction_sync()
        except Exception as err:
            ERROR_LOGGER.exception(
                "exception occurred in processing file. Aldar user directory {aldar_dir} \n "
                "Error Details are {error_details}".format(
                    aldar_dir=self.aldar_business_trigger_dir_name,
                    error_details=err
                )
            )
            raise


def process_sftp_business_trigger(aldar_dir):
    sftp = None
    try:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        # TODO: Discuss knownhost key
        # cnopts = pysftp.CnOpts(knownhosts='known_hosts')

        # sftp = pysftp.Connection(host=SFTP_SERVER_HOST, username=SFTP_USER_NAME, private_key=SSH_FILE_PATH, cnopts=cnopts)
        sftp = pysftp.Connection(host=SFTP_SERVER_HOST, username=SFTP_USER_NAME, cnopts=cnopts)
        try:
            aldar_csv_data_sync = AldarCSVDataSync(sftp, aldar_dir, constants.ALDAR_DIRECTORIES.get(aldar_dir))
            aldar_csv_data_sync.run()
        except Exception as err:
            ERROR_LOGGER.exception(
                "exception occurred in processing file. Aldar user directory {aldar_dir} \n "
                "Error Details are {error_details}".format(
                    aldar_dir=aldar_dir,
                    error_details=err
                )
            )
    except Exception as err:
        ERROR_LOGGER.exception(
            "exception occurred in processing file. Aldar user directory {aldar_dir} \n "
            "Error Details are {error_details}".format(
                aldar_dir=aldar_dir,
                error_details=err
            )
        )

    finally:
        session.close()
        engine.dispose()
        if sftp:
            sftp.close()


if __name__ == '__main__':
    command_line_parser = argparse.ArgumentParser(description='Aldar data sync')
    command_line_parser.add_argument(
        '-sftp_file_dir',
        help='SFTP file directory',
        default='',
        dest='sftp_file_dir'
    )
    inline_args = command_line_parser.parse_args()
    if inline_args.sftp_file_dir in constants.ALDAR_DIRECTORIES.keys():
        process_sftp_business_trigger(inline_args.sftp_file_dir)
    else:
        for _dir in constants.ALDAR_DIRECTORIES:
            process_sftp_business_trigger(_dir)
