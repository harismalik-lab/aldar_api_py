from cron_jobs import aldar_validation_schemas
ADR = 'ADR'
ALDAR_DIRECTORIES = {
    'aldreduenrlmntcncltns': dict(
        schema_class=aldar_validation_schemas.EducationEnrollmentCancellationSchema,
        model_class='EducationEnrollmentCancellation',
        asset='Education',
        log_file_date_keys=[dict(from_key='csv_timestamp', update_key='timestamp')],
        refund_api=True,
        csv_header=[
            'email',
            'mobile_number',
            'school_id',
            'school_name',
            'enrolment_id',
            'student_id',
            'payment_for',
            'cancellation_reference_number',
            'cancellation_fee',
            'refund_amount',
            'timestamp'
        ]
    ),
    'aldredupymnts': dict(
        schema_class=aldar_validation_schemas.EducationPaymentSchema,
        model_class='EducationPayment',
        asset='Education',
        log_file_date_keys=[dict(from_key='csv_timestamp', update_key='timestamp')],
        csv_header=[
            'email',
            'mobile_number',
            'school_id',
            'school_name',
            'enrolment_id',
            'student_id',
            'grade',
            'payment_reference_number',
            'payment_for',
            'charge_id',
            'description',
            'term_number',
            'is_student_enrolment_this_year',
            'gross_amount',
            'net_amount',
            'amount_paid_by_points',
            'paid_amount',
            'points_redemption_reference',
            'timestamp'
        ]
    ),
    'aldrlsnginstapymnts': dict(
        schema_class=aldar_validation_schemas.LeasingInstalmentPaymentsSchema,
        model_class='LeasingInstalmentPayments',
        asset='Leasing',
        log_file_date_keys=[
            dict(from_key='csv_payment_datetime', update_key='payment_datetime'),
            dict(from_key='csv_installment_due_date', update_key='installment_due_date')
        ],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'lease_contract_number',
            'is_renewal',
            'lease_method',
            'property_type',
            'contract_value',
            'contract_period_in_months',
            'number_of_installments',
            'payment_reference_number',
            'installment_number',
            'installment_due_date',
            'gross_amount',
            'net_amount',
            'amount_paid_by_points',
            'paid_amount',
            'points_redemption_reference',
            'payment_datetime'
        ]
    ),
    'aldrlsnginstapymntssls': dict(    # Leasing - Instalment Payments (by Sales)
        schema_class=aldar_validation_schemas.LeasingInstalmentPaymentsSchema,
        model_class='LeasingInstalmentPayments',
        asset='Leasing',
        log_file_date_keys=[
            dict(from_key='csv_payment_datetime', update_key='payment_datetime'),
            dict(from_key='csv_installment_due_date', update_key='installment_due_date')
        ],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'lease_contract_number',
            'is_renewal',
            'lease_method',
            'property_type',
            'contract_value',
            'contract_period_in_months',
            'number_of_installments',
            'payment_reference_number',
            'installment_number',
            'installment_due_date',
            'gross_amount',
            'net_amount',
            'amount_paid_by_points',
            'paid_amount',
            'points_redemption_reference',
            'payment_datetime'
        ]
    ),
    'aldrlsngslscncltns': dict(
        schema_class=aldar_validation_schemas.LeasingContractCancellationsSchema,
        model_class='LeasingContractCancellations',
        asset='Leasing',
        refund_api=True,
        log_file_date_keys=[dict(from_key='csv_cancellation_datetime', update_key='cancellation_datetime')],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'lease_contract_number',
            'cancellation_fee',
            'refund_amount',
            'cancellation_datetime'
        ]
    ),
    'aldrlsngslscncltnssls': dict(    # Leasing - Contract Cancellations (by Sales)
        schema_class=aldar_validation_schemas.LeasingContractCancellationsSchema,
        model_class='LeasingContractCancellations',
        asset='Leasing',
        refund_api=True,
        log_file_date_keys=[dict(from_key='csv_cancellation_datetime', update_key='cancellation_datetime')],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'lease_contract_number',
            'cancellation_fee',
            'refund_amount',
            'cancellation_datetime'
        ]
    ),
    # 'aldrlsngslssrvcpymnts': dict(
    #     schema_class=aldar_validation_schemas.LeasingCommunityServicesSchema,
    #     model_class='LeasingCommunityServices',
    #     asset='Leasing',
    #     log_file_date_keys=[dict(from_key='csv_payment_datetime', update_key='payment_datetime')],
    #     csv_header=[
    #         'email',
    #         'mobile_number',
    #         'community_id',
    #         'community_name',
    #         'unit_id',
    #         'lease_contract_number',
    #         'payment_reference_number',
    #         'payment_for',
    #         'service_facility_id',
    #         'description',
    #         'gross_amount',
    #         'net_amount',
    #         'amount_paid_by_points',
    #         'paid_amount',
    #         'points_redemption_reference',
    #         'payment_datetime'
    #     ]
    # ),
    'aldrmntnginstapymnts': dict(
        schema_class=aldar_validation_schemas.MaintenanceInstalmentPaymentsSchema,
        model_class='MaintenanceInstalmentPayments',
        asset='Maintenance',
        log_file_date_keys=[dict(from_key='csv_booking_datetime', update_key='booking_datetime')],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'maintenance_contract_number',
            'package_type',
            'package_id',
            'package_detail',
            'contract_value',
            'number_of_installments',
            'payment_reference_number',
            'installment_number',
            'property_type',
            'contract_period',
            'gross_amount',
            'net_amount',
            'amount_paid_by_points',
            'paid_amount',
            'points_redemption_reference',
            'booking_datetime'
        ]
    ),
    'aldrmntnlsngslscncltns': dict(
        schema_class=aldar_validation_schemas.MaintenanceContractCancellationsSchema,
        model_class='MaintenanceContractCancellations',
        asset='Maintenance',
        refund_api=True,
        log_file_date_keys=[dict(from_key='csv_cancellation_datetime', update_key='cancellation_datetime')],
        csv_header=[
            'email',
            'mobile_number',
            'community_id',
            'community_name',
            'unit_id',
            'maintenance_contract_number',
            'package_amount',
            'cancellation_fee',
            'refund_amount',
            'cancellation_datetime'
        ]
    ),
    'aldrslscncltns': dict(
        schema_class=aldar_validation_schemas.SalesContractCancellationsSchema,
        model_class='SalesContractCancellations',
        asset='Sales',
        refund_api=True,
        log_file_date_keys=[dict(from_key='csv_cancellation_datetime', update_key='cancellation_datetime')],
        csv_header=[
            'email',
            'mobile_number',
            'party_id',
            'community_id',
            'community_name',
            'unit_id',
            'sales_order_id',
            'cancellation_fee',
            'refund_amount',
            'cancellation_datetime'
        ]
    ),
    'aldrslsinstapymnts': dict(
        schema_class=aldar_validation_schemas.SalesInstalmentPaymentsSchema,
        model_class='SalesInstalmentPayments',
        asset='Sales',
        log_file_date_keys=[
            dict(from_key='csv_payment_datetime', update_key='payment_datetime'),
            dict(from_key='csv_order_date', update_key='order_date'),
            dict(from_key='csv_installment_due_date', update_key='installment_due_date')
        ],
        csv_header=[
            'email',
            'mobile_number',
            'party_id',
            'community_id',
            'community_name',
            'unit_id',
            'sales_order_id',
            'property_type',
            'property_gross_value',
            'property_net_value',
            'order_date',
            'number_of_installments',
            'payment_reference_number',
            'installment_number',
            'installment_due_date',
            'is_handover',
            'gross_amount',
            'net_amount',
            'amount_paid_by_points',
            'paid_amount',
            'points_redemption_reference',
            'payment_datetime'
        ]
    ),
    # 'aldrslssrvcpymnts': dict(
    #     schema_class=aldar_validation_schemas.SalesCommunityServicesSchema,
    #     model_class='SalesCommunityServices',
    #     asset='Sales',
    #     log_file_date_keys=[dict(from_key='csv_payment_datetime', update_key='payment_datetime')],
    #     csv_header=[
    #         'email',
    #         'mobile_number',
    #         'party_id',
    #         'community_id',
    #         'community_name',
    #         'unit_id',
    #         'sales_order_id',
    #         'payment_reference_number',
    #         'payment_for',
    #         'service_facility_id',
    #         'description',
    #         'gross_amount',
    #         'net_amount',
    #         'amount_paid_by_points',
    #         'paid_amount',
    #         'points_redemption_reference',
    #         'payment_datetime'
    #     ]
    # ),
}
ALDAR_APP = 'aldar_app'
ENTERTAINER_WEB = 'entertainer_web'
CONSOLIDATION = 'consolidation'
STATUS_PENDING = 0
STATUS_ERROR = 1
STATUS_PROCESSED = 2
