"""
Translation Manager
"""


class TranslationManager(object):

    @classmethod
    def get_translation(cls, translation_key, locale='en'):
        """
        Returns quick translated text in desired locale
        :param str translation_key: Translation constant name
        :param str locale: Desired translation
        :rtype: str
        """
        if cls._translations.get(translation_key):
            return cls._translations.get(translation_key).get(locale, '')
        return ''

    voucher_type_1 = 'VOUCHER_TYPE_Buy_One_Get_One_Free'
    voucher_type_2 = 'VOUCHER_TYPE_PERCENTAGE_OFF'
    voucher_type_3 = 'VOUCHER_TYPE_GIFT'
    voucher_type_4 = 'VOUCHER_TYPE_PACKAGE'
    voucher_type_5 = 'VOUCHER_TYPE_FIX_PRICE_OFF'
    voucher_type_6 = 'VOUCHER_TYPE_SPEND_THIS_GET_THIS'
    voucher_type_141 = 'VOUCHER_TYPE_Buy_One_Get_One_Free_141'

    voucher_restriction_1 = 'voucher_restriction_1_valid_for_dine_in_and_takeaway'
    voucher_restriction_2 = 'voucher_restriction_2_excluding_friday_brunch'
    voucher_restriction_3 = 'voucher_restriction_3_advance_booking_is_required'
    voucher_restriction_4 = 'voucher_restriction_4_delivery_only'
    voucher_restriction_5 = 'voucher_restriction_5_dine_in_only'
    voucher_restriction_6 = 'voucher_restriction_6_excluding_brunch'
    voucher_restriction_7 = 'voucher_restriction_7_food_only'
    voucher_restriction_8 = 'voucher_restriction_8_no_corkage_allowed'
    voucher_restriction_9 = 'voucher_restriction_9_not_valid_on_delivery'
    voucher_restriction_10 = 'voucher_restriction_10_not_valid_on_public_holidays'
    voucher_restriction_11 = 'voucher_restriction_11_rack_rate_applies'
    voucher_restriction_12 = 'voucher_restriction_12_to_redeem_you_must_be_of_legal_drinking_age_and_non_muslim'
    voucher_restriction_13 = 'voucher_restriction_13_valid_on_all_packages'
    voucher_restriction_14 = 'voucher_restriction_14_valid_on_delivery'

    Two_People = 'Two_People'
    NO = 'NO'
    YES = 'YES'
    OUTLET_SPECIFIC = "OUTLET_SPECIFIC"

    delivery_offers_remaining = 'delivery_offers_remaining'

    expired_offer = 'expired_offer'
    purchased_available_from = 'purchased_available_from'
    valid_to = 'valid_to'
    included_in_mobile_product_not_yet_purchased = 'included_in_mobile_product_not_yet_purchased'
    merchant_details_not_found = 'merchant_details_not_found'
    Wrong_Password_Login_Failure = 'Wrong_Password_Login_Failure'
    Time_Difference_Units = 'Time_Difference_Units'
    invalid_merchant_pin = 'invalid_merchant_pin'
    already_redeemed = 'already_redeemed'

    INVALID_PHONE = 'invalid_phone'
    INVALID_PHONE_OR_PASSWORD = 'invalid_phone_or_password'
    INVALID_PASSWORD = 'invalid_password'
    PASSWORD_MISMATCH = 'password_mismatch'
    PHONE_ALREADY_REGISTERED = 'p_a_r'
    INVALID_COMPANY = 'i_c'
    success = 'success'
    SUCCESS = 'success'
    INVALID_OTP = 'i_otp'
    USER_INACTIVE = 'u_i_a'
    UNABLE_TO_CHANGE_RESOURCE = 'u_t_c_r'
    INVALID_EMAIL = 'invalid_email'
    EMAIL_ALREADY_EXISTS = 'email_already_exists'
    MISMATCH_PASSWORDS = 'mismatch_passwords'
    ALREADY_USED_PASSWORD = 'already_used_password'
    INVALID_PASSWORD_RESET_TOKEN = 'invalid_password_reset_token'
    EXPIRED_PASSWORD_RESET_TOKEN = 'expired_password_reset_token'
    INVALID_SESSION_TOKEN = 'invalid_session_token'
    INVALID_CARD_BALANCE = "invalid_card_balance"
    INVLAID_REDEEM_AMOUNT = 'invlaid_redeem_amount'
    PROFILE_UPDATED_SUCCESSFULLY = 'profile_updated_successfully'
    SETTINGS_UPDATED = 'settings_updated'
    OTP_SENT_MESSAGE = 'otp_sent'
    OTP_RESEND_TIME_LIMIT = 'otp_resend_time_limit'
    PASSWORD_RESET_TITLE = 'password_reset_title'
    PASSWORD_RESET_EMAIL_SENT = 'password_reset_email_sent'
    SHARE_BUTTON_TITLE = 'share_button_title'
    REFERRAL_SECTION_MESSAGE = 'referral_section_message'
    DEVICE_BLOCKED_MESSAGE = "DEVICE_BLOCKED_MESSAGE"
    UNABLE_TO_BURN = 'unable_to_burn'
    UNABLE_TO_EARN = 'unable_to_earn'

    wrong_session_token = 'wrong_session_token'
    earn_not_enabled = 'earn_not_enabled'
    invalid_concept_id = "invalid_concept_id"

    INVALID_CLIENT = 'invalid_client'
    MOBILE_EMAIL_MISSING = "mobile_email_missing"
    USER_NOT_FOUND = "user_not_found"
    COUNTRY_UPDATED = "country_updated"

    _translations = {
        'invalid_phone': {
            'en': 'Invalid phone'
        },
        'invalid_client': {
            'en': 'Invalid Client.'
        },
        'p_a_r': {
            'en': 'Phone already registered'
        },
        "success": {
            "en": 'success',
            "ar": 'success',
            "cn": 'success',
            "el": 'success',
            "de": 'success'
        },
        'i_c': {
            'en': 'Invalid company'
        },
        'i_otp': {
            'en': 'Please enter correct PIN'
        },
        'u_i_a': {
            'en': 'User is inactive'
        },
        'u_t_c_r': {
            'en': 'Unable to change "{}".'
        },
        'invalid_phone_or_password': {
            'en': 'Invalid phone or password.'
        },
        'invalid_email': {
            'en': 'Invalid Email.'
        },
        'mismatch_passwords': {
            'en': 'New and confirm passwords are not same.'
        },
        'invalid_password_reset_token': {
            'en': 'Invalid password reset token.'
        },
        'expired_password_reset_token': {
            'en': 'Password reset token is expired.'
        },
        'already_used_password': {
            'en': 'Please enter some different password. You have recently used this password.'
        },
        'invalid_session_token': {
            'en': 'Invalid session token.'
        },
        'invalid_card_balance': {
            'en': 'card balance is not eligible for cashback redemption.'
        },
        'invlaid_redeem_amount': {
            'en': 'Reedeem amount for redemption is not eligible under card balance.'
        },
        'profile_updated_successfully': {
            'en': 'Profile updated successfully'
        },
        'settings_updated': {
            'en': 'Settings updated!'
        },
        'email_already_exists': {
            'en': 'An account with this email address already exists.'
        },
        'password_mismatch': {
            'en': 'Password you have entered does not match.'
        },
        'invalid_password': {
            'en': 'Invalid password. Please try again'
        },
        'otp_sent': {
            'en': 'OTP sent successfully.'
        },
        'otp_resend_time_limit': {
            'en': 'Please wait for {} seconds.'
        },
        'password_reset_email_sent': {
            'en': 'We have sent you a link to your email to reset your password'
        },
        'password_reset_title': {
            'en': "We've sent an email"
        },
        "VOUCHER_TYPE_Buy_One_Get_One_Free": {
            'en': 'Buy 1 Get 1 Free',
            'ar': 'Buy 1 Get 1 Free',
            'el': 'Buy 1 Get 1 Free',
            'cn': 'Buy 1 Get 1 Free',
            'de': 'Buy 1 Get 1 Free'
        },
        "VOUCHER_TYPE_PERCENTAGE_OFF": {
            'en': '_percentage_value_% Off',
            'ar': '_percentage_value_% Off',
            'el': '_percentage_value_% Off',
            'cn': '_percentage_value_% Off',
            'de': '_percentage_value_% Off'
        },
        "VOUCHER_TYPE_SPEND_THIS_GET_THIS": {
            'en': 'Spend _spend_value_ Get _reward_value_',
            'ar': 'Spend _spend_value_ Get _reward_value_',
            'el': 'Spend _spend_value_ Get _reward_value_',
            'cn': 'Spend _spend_value_ Get _reward_value_',
            'de': 'Spend _spend_value_ Get _reward_value_'
        },
        "VOUCHER_TYPE_Buy_One_Get_One_Free_141": {
            'en': 'Buy 1 Get 1 Free',
            'ar': 'اشتر واحداً واحصل على الثاني مجاناً',
            'el': 'Αγοράστε Ένα, Πάρτε Ένα Δωρεάν',
            'cn': '買一送一',
            'de': 'Buy 1 Get 1 Free'
        },
        "VOUCHER_TYPE_GIFT": {
            'en': 'Gift',
            'ar': 'Gift',
            'el': 'Gift',
            'cn': 'Gift',
            'de': 'Gift'
        },
        "VOUCHER_TYPE_PACKAGE": {
            'en': 'Package',
            'ar': 'صفقة',
            'el': 'Package',
            'cn': 'Package',
            'de': 'Package'
        },
        "VOUCHER_TYPE_FIX_PRICE_OFF": {
            'en': '_discount_value_ Off',
            'ar': '_discount_value_ Off',
            'el': '_discount_value_ Off',
            'cn': '_discount_value_ Off',
            'de': '_discount_value_ Off'
        },
        "voucher_restriction_1_valid_for_dine_in_and_takeaway": {
            "en": 'Valid for Dine-in and Take-Away',
            "ar": 'Valid for Dine-in and Take-Away',
            "cn": 'Valid for Dine-in and Take-Away',
            "el": 'Valid for Dine-in and Take-Away',
            "de": 'Valid for Dine-in and Take-Away'
        },
        "voucher_restriction_2_excluding_friday_brunch": {
            "en": 'Excluding Friday Brunch',
            "ar": 'Excluding Friday Brunch',
            "cn": 'Excluding Friday Brunch',
            "el": 'Excluding Friday Brunch',
            "de": 'Excluding Friday Brunch'
        },
        "voucher_restriction_3_advance_booking_is_required": {
            "en": 'Advance Booking is Required',
            "ar": 'Advance Booking is Required',
            "cn": 'Advance Booking is Required',
            "el": 'Advance Booking is Required',
            "de": 'Advance Booking is Required'
        },
        "voucher_restriction_4_delivery_only": {
            "en": 'Delivery only',
            "ar": 'Delivery only',
            "cn": 'Delivery only',
            "el": 'Delivery only',
            "de": 'Delivery only'
        },
        "voucher_restriction_5_dine_in_only": {
            "en": 'Dine-in only',
            "ar": 'Dine-in only',
            "cn": 'Dine-in only',
            "el": 'Dine-in only',
            "de": 'Dine-in only'
        },
        "voucher_restriction_6_excluding_brunch": {
            "en": 'Excluding Brunch',
            "ar": 'Excluding Brunch',
            "cn": 'Excluding Brunch',
            "el": 'Excluding Brunch',
            "de": 'Excluding Brunch'
        },
        "voucher_restriction_7_food_only": {
            "en": 'Food only',
            "ar": 'Food only',
            "cn": 'Food only',
            "el": 'Food only',
            "de": 'Food only'
        },
        "voucher_restriction_8_no_corkage_allowed": {
            "en": 'No Corkage Allowed',
            "ar": 'No Corkage Allowed',
            "cn": 'No Corkage Allowed',
            "el": 'No Corkage Allowed',
            "de": 'No Corkage Allowed'
        },
        "voucher_restriction_9_not_valid_on_delivery": {
            "en": 'Not Valid on Delivery',
            "ar": 'Not Valid on Delivery',
            "cn": 'Not Valid on Delivery',
            "el": 'Not Valid on Delivery',
            "de": 'Not Valid on Delivery'
        },
        "voucher_restriction_10_not_valid_on__holidays": {
            "en": 'Not Valid on  Holidays',
            "ar": 'Not Valid on  Holidays',
            "cn": 'Not Valid on  Holidays',
            "el": 'Not Valid on  Holidays',
            "de": 'Not Valid on  Holidays'
        },
        "voucher_restriction_11_rack_rate_applies": {
            "en": 'Rack Rate Applies',
            "ar": 'Rack Rate Applies',
            "cn": 'Rack Rate Applies',
            "el": 'Rack Rate Applies',
            "de": 'Rack Rate Applies'
        },
        "voucher_restriction_12_to_redeem_you_must_be_of_legal_drinking_age_and_non_muslim": {
            "en": 'To redeem you must be of legal drinking age and non-Muslim',
            "ar": 'To redeem you must be of legal drinking age and non-Muslim',
            "cn": 'To redeem you must be of legal drinking age and non-Muslim',
            "el": 'To redeem you must be of legal drinking age and non-Muslim',
            "de": 'To redeem you must be of legal drinking age and non-Muslim'
        },
        "voucher_restriction_13_valid_on_all_packages": {
            "en": 'Valid on All Packages',
            "ar": 'Valid on All Packages',
            "cn": 'Valid on All Packages',
            "el": 'Valid on All Packages',
            "de": 'Valid on All Packages'
        },
        "voucher_restriction_14_valid_on_delivery": {
            "en": 'Valid on Delivery',
            "ar": 'Valid on Delivery',
            "cn": 'Valid on Delivery',
            "el": 'Valid on Delivery',
            "de": 'Valid on Delivery'
        },
        'delivery_offers_remaining': {
            "en": "Offer(s) Remaining",
            "ar": "عدد العروض المتبقية",
            "cn": "Offer(s) Remaining",
            "el": "Offer(s) Remaining",
            "de": "Offer(s) Remaining"
        },
        'NO': {
            'en': 'No',
            'ar': 'لا',
            'el': 'ΟΧΙ',
            'cn': '沒有'
        },
        'YES': {
            'en': 'Yes',
            'ar': 'نعم',
            'el': 'ΝΑΙ',
            'cn': '是'
        },
        'OUTLET_SPECIFIC': {
            'en': 'Outlet Specific',
            'ar': 'محدد من المنفذ',
            'el': 'Συγκεκριμένο Κατάστημα',
            'cn': '視乎分店'
        },
        'expired_offer': {
            "en": "This offer has expired",
            "ar": "ها العرض منتهي",
            "cn": "此優惠已到期",
            "el": "Αυτή η προσφορά έχει λήξει",
            "de": "This offer has expired"
        },
        'purchased_available_from': {
            "en": "PURCHASED, AVAILABLE FROM APP_DATE",
            "ar": "تم شراؤه، متوافر من APP_DATE",
            "cn": "已購買，由APP_DATE開始適用",
            "el": "ΕΧΕΙ ΑΓΟΡΑΣΤΕΙ, ΔΙΑΘΕΣΙΜΟ ΣΤΟ APP_DATE",
            "de": "PURCHASED, AVAILABLE FROM APP_DATE"
        },
        'valid_to': {
            "en": "VALID TO APP_DATE",
            "ar": "APP_DATE صالح حتى",
            "cn": "有效期至APP_DATE",
            "el": "ΙΣΧΥΕΙ ΕΩΣ APP_DATE",
            "de": "VALID TO APP_DATE"
        },
        'included_in_mobile_product_not_yet_purchased': {
            "en": "INCLUDED IN MOBILE PRODUCT NOT YET PURCHASED",
            "ar": "مدرج في منتج المحمول ولم يتم شراؤه بعد",
            "cn": "包含在未購買的流動產品",
            "el": "ΠΕΡΙΛΑΜΒΑΝΕΤΑΙ ΣΕ ΠΡΟΪΟΝ ΓΙΑ ΚΙΝΗΤΑ ΠΟΥ ΔΕΝ ΕΧΕΙ ΑΓΟΡΑΣΤΕΙ ΑΚΟΜΗ",
            "de": "INCLUDED IN MOBILE PRODUCT NOT YET PURCHASED"
        },
        'merchant_details_not_found': {
            "en": "Merchant details not found.",
            "ar": "Merchant details not found.",
            "cn": "Merchant details not found.",
            "el": "Merchant details not found.",
            "de": "Merchant details not found."
        },
        'wrong_session_token': {
            "en": "Wrong session_token",
            "ar": "خطأ في الصفحة_قسيمة",
            "cn": "會話錯誤_代幣",
            "el": "Wrong session_token",
            "de": "Wrong session_token"
        },
        'earn_not_enabled': {
            "en": "Earn for given outlet is not enabled."
        },
        'invalid_merchant_pin': {
            "en": "Invalid merchant PIN",
            "ar": "رمز التعريف الشخصي الخاص بالتاجر غير صحيح",
            "cn": "商戶私人密碼無效。",
            "el": "Λάθος ΡΙΝ Εμπόρου",
            "de": "Invalid merchant PIN"
        },
        'invalid_concept_id': {
            "en": 'Invalid Concept Id'
        },
        #######################
        # Heading translations
        #######################
        "Two_People": {
            "en": "2 PEOPLE",
            "ar": "2 PEOPLE",
            "el": "2 PEOPLE",
            "cn": "2 PEOPLE",
            "de": "2 PEOPLE"
        },
        'share_button_title': {
            'en': "Refer A Friend"
        },
        'referral_section_message': {
            'en': "Share Darna with friends and family today. Don’t keep all that moneysaving to yourself!"
        },
        "Wrong_Password_Login_Failure": {
            "en": "Due to password being entered wrong, your account has been locked. "
                  "Please wait for {time} to try again.",
            "ar": "لقد تم تعليق حسابك نتيجة إدخال كلمة مرور خاطئة. يرجى الانتظار لـ {time} قبل المحاولة مجدداً",
            "el": "Λόγω του λάθους κωδικού πρόσβασης που έχει εισαχθεί, ο λογαριασμός σας έχει κλειδωθεί. Περιμένετε "
                  "{time} για να δοκιμάσετε ξανά",
            "cn": "由於密碼輸入錯誤，你的帳戶已被鎖定。 請等候 {time}，再作嘗試。",
            "de": "Due to password being entered wrong, your account has been locked. "
                  "Please wait for {time} to try again.",
        },
        "Time_Difference_Units": {
            "en": ["days", "hours", "minutes", "seconds"],
            "ar": ["days", "hours", "minutes", "ثانية"],
            "el": ["days", "hours", "minutes", "δευτερόλεπτα"],
            "cn": ["days", "hours", "minutes", "秒"],
            "de": ["days", "hours", "minutes", "seconds"],
        },
        "DEVICE_BLOCKED_MESSAGE": {
            "en": "Device is blocked for 30 minutes.",
            "ar": "Device is blocked for 30 minutes.",
            "el": "Device is blocked for 30 minutes.",
            "cn": "Device is blocked for 30 minutes."
        },
        'unable_to_burn': {'en': 'Unable to burn points please try later.'},
        'unable_to_earn': {'en': 'Unable to earn points please try later.'},
        'already_redeemed': {
            "en": "ALREADY REDEEMED",
            "ar": "تم استخدامه",
            "cn": "已兌換",
            "el": "ΕΧΕΙ ΗΔΗ ΕΞΑΡΓΥΡΩΘΕΙ",
            "de": "ALREADY REDEEMED"
        },
        "mobile_email_missing": {
            "en": "mobile_number/email: missing required parameter"
        },
        "user_not_found": {
            "en": "User not found"
        },
        "country_updated": {
            "en": "Country of Residence updated!"
        },

    }
