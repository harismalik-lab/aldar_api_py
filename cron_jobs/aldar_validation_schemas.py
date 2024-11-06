import datetime

from marshmallow import Schema, fields, pre_load, post_dump, validate


class EducationPaymentSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    school_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    school_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    enrolment_id = fields.Int(required=True)
    student_id = fields.Int(required=True)
    grade = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    payment_for = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    charge_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    term_number = fields.Int(required=True, validate=validate.Range(min=0))
    is_student_enrolment_this_year = fields.Boolean(required=True)
    gross_amount = fields.Float(required=True, validate=validate.Range(min=0))
    net_amount = fields.Float(required=True, validate=validate.Range(min=0))
    amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
    paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
    points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    timestamp = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    csv_timestamp = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(school_name='School Name',
                                         description='NA',
                                         term_number=0,
                                         is_student_enrolment_this_year=0,
                                         net_amount=0,
                                         amount_paid_by_points=0,
                                         paid_amount=0,
                                         points_redemption_reference='NA')

        strip_comma_from_amount_column = ['gross_amount', 'net_amount', 'amount_paid_by_points', 'paid_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_timestamp'] = data['timestamp']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = data['payment_for']
        data['business_category'] = 'Education'
        data['concept_id'] = data['school_id']
        data['concept_name'] = data['school_name']
        data['external_transaction_id'] = data['payment_reference_number']
        data['currency'] = 'AED'
        data['gross_total_amount'] = data['gross_amount']
        data['amount_paid_using_points'] = data['amount_paid_by_points']
        data['redemption_reference'] = data['points_redemption_reference']
        data['transaction_datetime'] = data['timestamp'].replace('T', ' ')
        data['is_student_enrolment_this_year'] = 1 if data['is_student_enrolment_this_year'] else 0
        if data['payment_for'] == 'education_term_fee':
            data['is_progressed_from_primary_to_secondary'] = 0
            if data['payment_for'] == 'education_term_fee' and data['term_number'] == 1 and data['is_student_enrolment_this_year'] == 0 and data['grade'] in ("Year 07", "Grade 06"):
                data['is_progressed_from_primary_to_secondary'] = 1
        return data


class EducationEnrollmentCancellationSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    school_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    school_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    enrolment_id = fields.Int(required=True)
    student_id = fields.Int(required=True)
    payment_for = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    cancellation_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    cancellation_fee = fields.Float(required=True, validate=validate.Range(min=0))
    refund_amount = fields.Float(required=True, validate=validate.Range(min=0))
    timestamp = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    csv_timestamp = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(school_name='School Name',
                                         cancellation_fee=0,
                                         refund_amount=0)
        strip_comma_from_amount_column = ['cancellation_fee', 'refund_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_timestamp'] = data['timestamp']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = data['payment_for']
        data['business_category'] = 'Education'
        data['concept_id'] = data['school_id']
        data['concept_name'] = data['school_name']
        data['transaction_id'] = '{}#{}'.format(data['school_id'], data['cancellation_reference_number'])
        data['currency'] = 'AED'
        data['refund_points_mode'] = 'amount'
        data['value'] = data['refund_amount']
        data['description'] = 'Education refund api call with SFTP data from TE to LMS'

        return data


class LeasingInstalmentPaymentsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    payment_for = fields.Str(dump_only=True)
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    lease_contract_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    is_renewal = fields.Boolean(required=True)
    lease_method = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    property_type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    contract_value = fields.Float(required=True, validate=validate.Range(min=0))
    contract_period_in_months = fields.Int(required=True)
    number_of_installments = fields.Int(required=True)
    payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    installment_number = fields.Int(required=True)
    installment_due_date = fields.Date(required=True, format='%d-%m-%Y')
    csv_installment_due_date = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    gross_amount = fields.Float(required=True, validate=validate.Range(min=0))
    net_amount = fields.Float(required=True, validate=validate.Range(min=0))
    amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
    paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
    points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    payment_datetime = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    csv_payment_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(is_renewal=0,
                                         gross_amount=0,
                                         net_amount=0,
                                         amount_paid_by_points=0,
                                         paid_amount=0,
                                         points_redemption_reference='NA')

        strip_comma_from_amount_column = ['contract_value', 'gross_amount', 'net_amount', 'amount_paid_by_points',
                                          'paid_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_payment_datetime'] = data['payment_datetime']
        data['csv_installment_due_date'] = data['installment_due_date']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = data['payment_for']
        data['business_category'] = 'Leasing'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['external_transaction_id'] = data['payment_reference_number']
        data['number_of_instalments'] = data['number_of_installments']
        data['instalment_due_date'] = datetime.datetime.strptime(data['installment_due_date'], '%d-%m-%Y').strftime(
            '%Y-%m-%d'
        )
        data['instalment_number'] = data['installment_number']
        data['currency'] = 'AED'
        data['gross_total_amount'] = data['gross_amount']
        data['amount_paid_using_points'] = data['amount_paid_by_points']
        data['redemption_reference'] = data['points_redemption_reference']
        data['transaction_datetime'] = data['payment_datetime'].replace('T', ' ')
        data['is_renewal'] = 1 if data['is_renewal'] else 0
        data['contract_period'] = data['contract_period_in_months']
        data['description'] = 'Leasing earn api call with SFTP data from TE to LMS'
        data['charge_id'] = '100'

        return data


# class LeasingCommunityServicesSchema(Schema):
#     id = fields.Int(dump_only=True)
#     user_id = fields.Int(dump_only=True)
#     email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
#     mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
#     community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
#     community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     lease_contract_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     payment_for = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     service_facility_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     gross_amount = fields.Float(required=True)
#     net_amount = fields.Float(required=True)
#     amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
#     paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
#     points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     payment_datetime = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
#     csv_payment_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
#     file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#
#     class Meta:
#         default_values_and_fields = dict(description='NA',
#                                          amount_paid_by_points=0,
#                                          paid_amount=0,
#                                          points_redemption_reference='NA')
#
#     @pre_load
#     def pre_process(self, data, **kwargs):
#         for key, value in self.Meta.default_values_and_fields.items():
#             if key in data.keys() and not data[key]:
#                 data[key] = value
#
#         data['csv_payment_datetime'] = data['payment_datetime']
#
#         return data
#
#     @post_dump
#     def post_dump(self, data, **kwargs):
#         data['business_trigger'] = data['payment_for']
#         data['business_category'] = 'Leasing'
#         data['concept_id'] = data['community_id']
#         data['concept_name'] = data['community_name']
#         data['external_transaction_id'] = data['payment_reference_number']
#         data['currency'] = 'AED'
#         data['gross_total_amount'] = data['gross_amount']
#         data['amount_paid_using_points'] = data['amount_paid_by_points']
#         data['redemption_reference'] = data['points_redemption_reference']
#         data['transaction_datetime'] = data['payment_datetime'].replace('T', ' ')
#         data['charge_id'] = '100'
#         return data


class LeasingContractCancellationsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    lease_contract_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    cancellation_fee = fields.Float(required=True, validate=validate.Range(min=0))
    refund_amount = fields.Float(required=True, validate=validate.Range(min=0))
    cancellation_datetime = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    csv_cancellation_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(cancellation_fee=0, refund_amount=0)
        strip_comma_from_amount_column = ['cancellation_fee', 'refund_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_cancellation_datetime'] = data['cancellation_datetime']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = 'leasing_instalment_payment'
        data['business_category'] = 'Leasing'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['transaction_id'] = '{}#{}'.format(data['community_id'], data['lease_contract_number'])
        data['currency'] = 'AED'
        data['refund_points_mode'] = 'amount'
        data['value'] = data['refund_amount']
        data['description'] = 'Leasing refund api call with SFTP data from TE to LMS'
        return data


class MaintenanceInstalmentPaymentsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    maintenance_contract_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    package_type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    package_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    package_detail = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    contract_value = fields.Float(required=True)
    number_of_installments = fields.Int(required=True)
    payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    installment_number = fields.Int(required=True)
    property_type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    contract_period = fields.Int(required=True, validate=validate.Range(min=0))
    gross_amount = fields.Float(required=True, validate=validate.Range(min=0))
    net_amount = fields.Float(required=True, validate=validate.Range(min=0))
    amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
    paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
    points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    csv_booking_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    booking_datetime = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(contract_period=0,
                                         gross_amount=0,
                                         net_amount=0,
                                         amount_paid_by_points=0,
                                         paid_amount=0,
                                         points_redemption_reference='NA')
        strip_comma_from_amount_column = ['contract_value', 'gross_amount', 'net_amount', 'amount_paid_by_points',
                                          'paid_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_booking_datetime'] = data['booking_datetime']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = 'maintenance_instalment_payment'
        data['business_category'] = 'Maintenance'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['number_of_instalments'] = data['number_of_installments']
        data['instalment_number'] = data['installment_number']
        data['external_transaction_id'] = data['payment_reference_number']
        data['currency'] = 'AED'
        data['gross_total_amount'] = data['gross_amount']
        data['amount_paid_using_points'] = data['amount_paid_by_points']
        data['redemption_reference'] = data['points_redemption_reference']
        data['transaction_datetime'] = data['booking_datetime'].replace('T', ' ')
        data['description'] = 'Maintenance earn api call with SFTP data from TE to LMS'
        data['charge_id'] = '100'

        return data


class MaintenanceContractCancellationsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    maintenance_contract_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    package_amount = fields.Float(required=True)
    cancellation_fee = fields.Float(required=True, validate=validate.Range(min=0))
    refund_amount = fields.Float(required=True, validate=validate.Range(min=0))
    cancellation_datetime = fields.AwareDateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
    csv_cancellation_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(cancellation_fee=0, refund_amount=0)
        strip_comma_from_amount_column = ['package_amount', 'cancellation_fee', 'refund_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_cancellation_datetime'] = data['cancellation_datetime']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = 'maintenance_instalment_payment'
        data['business_category'] = 'Maintenance'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['transaction_id'] = '{}#{}'.format(data['community_id'], data['maintenance_contract_number'])
        data['currency'] = 'AED'
        data['refund_points_mode'] = 'amount'
        data['value'] = data['refund_amount']
        data['description'] = 'Maintenance refund api call with SFTP data from TE to LMS'
        return data


class SalesInstalmentPaymentsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    party_id = fields.Int(required=True)
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    payment_for = fields.Str(dump_only=True)
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    sales_order_id = fields.Int(required=True)
    property_type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    property_gross_value = fields.Float(required=True)
    property_net_value = fields.Float(required=True)
    order_date = fields.Date(required=True, format='%d-%m-%Y')
    csv_order_date = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    number_of_installments = fields.Int(required=True)
    payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    installment_number = fields.Int(required=True)
    installment_due_date = fields.Date(required=True, format='%d-%m-%Y')
    csv_installment_due_date = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    is_handover = fields.Boolean(required=True)
    gross_amount = fields.Float(required=True)
    net_amount = fields.Float(required=True)
    amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
    paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
    points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    payment_datetime = fields.DateTime(required=True, format='%d-%m-%Y:%H:%M:%S')
    csv_payment_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(is_handover=0,
                                         amount_paid_by_points=0,
                                         paid_amount=0,
                                         points_redemption_reference='NA')
        strip_comma_from_amount_column = ['property_gross_value', 'property_net_value', 'gross_amount', 'net_amount',
                                          'amount_paid_by_points', 'paid_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_payment_datetime'] = data['payment_datetime']
        data['csv_order_date'] = data['order_date']
        data['csv_installment_due_date'] = data['installment_due_date']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = data['payment_for']
        data['business_category'] = 'Sales'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['number_of_instalments'] = data['number_of_installments']
        data['instalment_due_date'] = datetime.datetime.strptime(data['installment_due_date'], '%d-%m-%Y').strftime(
            '%Y-%m-%d'
        )
        data['order_date'] = datetime.datetime.strptime(data['order_date'], '%d-%m-%Y').strftime('%Y-%m-%d')
        data['instalment_number'] = data['installment_number']
        data['external_transaction_id'] = data['payment_reference_number']
        data['currency'] = 'AED'
        data['gross_total_amount'] = data['gross_amount']
        data['amount_paid_using_points'] = data['amount_paid_by_points']
        data['redemption_reference'] = data['points_redemption_reference']
        data['is_handover_payment'] = 1 if data['is_handover'] else 0
        data['transaction_datetime'] = data['payment_datetime'].replace('T', ' ')
        data['transaction_datetime'] = datetime.datetime.strptime(
            data['payment_datetime'], '%d-%m-%Y:%H:%M:%S'
        ).strftime('%Y-%m-%d %H:%M:%S')
        data['description'] = 'Sales earn api call with SFTP data from TE to LMS'
        data['charge_id'] = '100'

        return data


# class SalesCommunityServicesSchema(Schema):
#     id = fields.Int(dump_only=True)
#     user_id = fields.Int(dump_only=True)
#     email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
#     mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
#     party_id = fields.Int(required=True)
#     community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
#     community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     sales_order_id = fields.Int(required=True)
#     payment_reference_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     payment_for = fields.Str(required=True, validate=validate.Length(min=1, max=30))
#     service_facility_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
#     description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     gross_amount = fields.Float(required=True)
#     net_amount = fields.Float(required=True)
#     amount_paid_by_points = fields.Float(required=True, validate=validate.Range(min=0))
#     paid_amount = fields.Float(required=True, validate=validate.Range(min=0))
#     points_redemption_reference = fields.Str(required=True, validate=validate.Length(min=1, max=50))
#     payment_datetime = fields.DateTime(required=True, format='%Y-%m-%dT%H:%M:%S%z')
#     csv_payment_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
#     file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#     unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))
#
#     class Meta:
#         default_values_and_fields = dict(description='NA',
#                                          amount_paid_by_points=0,
#                                          paid_amount=0,
#                                          points_redemption_reference='NA')
#
#     @pre_load
#     def pre_process(self, data, **kwargs):
#         for key, value in self.Meta.default_values_and_fields.items():
#             if key in data.keys() and not data[key]:
#                 data[key] = value
#
#         data['csv_payment_datetime'] = data['payment_datetime']
#
#         return data
#
#     @post_dump
#     def post_dump(self, data, **kwargs):
#         data['business_trigger'] = data['payment_for']
#         data['business_category'] = 'Sales'
#         data['concept_id'] = data['community_id']
#         data['concept_name'] = data['community_name']
#         data['external_transaction_id'] = data['payment_reference_number']
#         data['currency'] = 'AED'
#         data['gross_total_amount'] = data['gross_amount']
#         data['amount_paid_using_points'] = data['amount_paid_by_points']
#         data['redemption_reference'] = data['points_redemption_reference']
#         data['transaction_datetime'] = data['payment_datetime'].replace('T', ' ')
#         data['charge_id'] = '100'
#         return data


class SalesContractCancellationsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    mobile_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    party_id = fields.Int(required=True)
    community_id = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    community_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unit_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    sales_order_id = fields.Int(required=True)
    cancellation_fee = fields.Float(required=True, validate=validate.Range(min=0))
    refund_amount = fields.Float(required=True, validate=validate.Range(min=0))
    cancellation_datetime = fields.DateTime(required=True, format='%d-%m-%Y:%H:%M:%S')
    csv_cancellation_datetime = fields.Str(required=True, validate=validate.Length(min=1, max=25))
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    unique_file_identifier = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    class Meta:
        default_values_and_fields = dict(cancellation_fee=0, refund_amount=0)
        strip_comma_from_amount_column = ['cancellation_fee', 'refund_amount']

    @pre_load
    def pre_process(self, data, **kwargs):
        for key, value in data.items():
            data[key] = value.strip()

        for key in self.Meta.strip_comma_from_amount_column:
            data[key] = data[key].replace(',', '')

        for key, value in self.Meta.default_values_and_fields.items():
            if key in data.keys() and not data[key]:
                data[key] = value

        data['csv_cancellation_datetime'] = data['cancellation_datetime']

        return data

    @post_dump
    def post_dump(self, data, **kwargs):
        data['business_trigger'] = 'sales_instalment_payment'
        data['business_category'] = 'Sales'
        data['concept_id'] = data['community_id']
        data['concept_name'] = data['community_name']
        data['transaction_id'] = '{}#{}'.format(data['community_id'], data['sales_order_id'])
        data['currency'] = 'AED'
        data['refund_points_mode'] = 'amount'
        data['value'] = data['refund_amount']
        data['description'] = 'Sales refund api call with SFTP data from TE to LMS'
        return data
