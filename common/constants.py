"""
Common constants reside here
"""
from flask import current_app

INTERNAL_SERVER_ERROR = 'Internal Server Error'
LOG_SUB_FOLDERS = []
ALDAR = 'aldar'
ALDAR_APP = 'aldar_app'
ENTERTAINER_WEB = 'entertainer_web'
CONSOLIDATION = 'consolidation'
DEFAULT_DATE_FORMAT = "%Y/%m/%d"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
EN, AR, DE, CN, EL, ZH = 'en', 'ar', 'de', 'cn', 'el', 'zh'
FIRST_TIME_REGISTRATION_REQUIRED_AND_TRUE_FIELDS = (
    'gdpr_privacy_policy', 'terms_and_conditions'
)
FIRST_TIME_REGISTRATION_REQUIRED_FIELDS = (
    'first_name', 'last_name', 'email', 'password', 'confirm_password'
)
MEMBERSHIP_CODE_DEFAULT_CARD_NUMBER = 1
MEMBERSHIP_CODE_DEFAULT_LOCATION = "XX"
MEMBERSHIP_CODE_PREFIX = 'M'
SUPPORTED_LOCALES = (DE, EN, AR, CN, EL, ZH)
AED = 'AED'
USD = 'USD'
VALID_CURRENCIES = ("BHD", "EGP", "EUR", "GBP", "HKD", "JOD", "KWD", "LBP",
                    "MYR", "OMR", "QAR", "SAR", "SGD", USD, "ZAR", AED)
OTP_RATE_LIMIT_SECONDS = 30
OTP_EXPIRATION_IN_MINUTES = 30
# CUSTOM ERROR CODES
PHONE_ALREADY_EXISTS = 10
INVALID_COMPANY = 11
OTP_RELATED_ISSUE = 12
USER_INACTIVE = 13
PASSWORD_CHANGE_FLOW_REQUIRED = 14
INVALID_EMAIL = 15
MISMATCH_PASSWORDS = 16
INVALID_PASSWORD_RESET_TOKEN = 17
EXPIRED_PASSWORD_RESET_TOKEN = 18
INVALID_CARD_ERR_CODE = 19
INVALID_BALANCE_ERR_CODE = 20
CAPTCHA_FAILED_ERR_CODE = 70
EARN_NOT_ENABLED_ERR_CODE = 77
INVALID_MERCHANT_PIN_ERR_CODE = 78
INVALID_CONCEPT_ID_ERR_CODE = 76
INVALID_CLIENT_ERR_CODE = 88
MISSING_PARAMETER_ERR_CODE = 90
USER_NOT_FOUND_ERR_CODE = 89

OTP_START_RANGE = 10000
OTP_END_RANGE = 99999

CATEGORY_NAME_BODY = 'Body'
CATEGORY_NAME_LEISURE = 'Leisure'
CATEGORY_NAME_RESTAURANTS_AND_BARS = 'Restaurants and Bars'
CATEGORY_NAME_RETAIL = 'Retail'
CATEGORY_NAME_SERVICES = 'Services'
CATEGORY_NAME_TRAVEL = 'Travel'

CATEGORY_API_NAME_BODY = 'Body'
CATEGORY_API_NAME_LEISURE = 'Leisure'
CATEGORY_API_NAME_RESTAURANTS_AND_BARS = 'Restaurants and Bars'
CATEGORY_API_NAME_RETAIL = 'Retail'
CATEGORY_API_NAME_SERVICES = 'Services'
CATEGORY_API_NAME_TRAVEL = 'Travel'
CATEGORY_API_NAME_KIDS = 'Kids'
CATEGORY_API_NAME_SHOPPING = 'shopping'
CATEGORY_API_NAME_HOTELS = 'hotels'

LISTING_TYPE_SUBCATEGORY = 'subcategory'
LISTING_TYPE_CATEGORY = 'category'

ALL_MALLS = "All Locations"
ALL_HOTELS = "All Hotels"
MALLS = "malls"
HOTELS = "hotels"
ADR = 'ADR'
CLO = 'CLO'

INVALID_TOKEN = "Token is not valid"
INVALID_JWT = "Unauthorized JWT Token"
INVALID_PARAMS = 'Invalid parameters'

MAX_OUTLETS = 60

SECTION_IDENTIFIER = 'section_identifier'
SUB_CATEGORIES = 'sub_categories'
DROPDOWN = 'dropdown'
DROPDOWN_ITEMS = 'dropdown_items'

PASSWORD_RESET_EXPIRATION_IN_HOURS = 2
CATEGORIES_WITHOUT_CHILDREN = ('spas',)
CUSTOM_ERROR_CODE = 70

MERCHANT_ATTRIBUTES_BODY = [
    'by_appointment_only',
    'certified',
    'female_only',
    'couples_friendly',
    'indoor_facilities',
    'jacuzzi',
    'kids_play_area',
    'male_only',
    'moroccan_bath',
    'outdoor_facilities',
    'personal_trainer',
    'refreshments',
    'pool',
    'sauna',
    'steam_room',
    'supervised_play_area',
    'parking',
    'valet_parking'
]

MERCHANT_ATTRIBUTES_LEISURE = [
    'age_restrictions',
    'aviation',
    'desert_safari',
    'fishing',
    'height_restrictions',
    'indoor_activities',
    'kids_welcome',
    'motor_sports',
    'outdoor_activities',
    'parking',
    'team_sports',
    'valet_parking',
    'alcohol',
    'boating',
    'extreme_sports',
    'golf',
    'holiday_programmes',
    'indoor_play_area',
    'live_entertainment',
    'outdoor_cooling',
    'outdoor_play_area',
    'racquet_sports',
    'rooftop_bars',
    'theme_park',
    'water_park',
    'water_sports',
    'wineries'
]

MERCHANT_ATTRIBUTES_RESTAURANTS_AND_BARS = [
    'alcohol',
    'brunch',
    'buffet',
    'cuisine',
    'delivery',
    'dress_code',
    'fine_dining',
    'groups_welcome',
    'halal',
    'hubbly_bubbly',
    'kids_welcome',
    'live_entertainment',
    'open_late',
    'outdoor_cooling',
    'outdoor_heating',
    'outdoor_seating',
    'parking',
    'pets_allowed',
    'pork_products',
    'price_range',
    'rooftop_bars',
    'smoking_indoor',
    'smoking_outdoor',
    'smoking_shisha',
    'sports_screens',
    'supervised_play_area',
    'takeaway',
    'valet_parking',
    'wheelchair_accessible',
    'wi_fi',
    'wineries',
    'with_a_view'
]

MERCHANT_ATTRIBUTES_SERVICES = [
    'beauty_products',
    'by_appointment_only',
    'delivery',
    'pharmacy',
    'pick_up_drop_off'
]

MERCHANT_ATTRIBUTES_TRAVEL = [
    'x24_hour_reception',
    'x24_hour_room_service',
    'air_conditioning',
    'alcohol',
    'balcony',
    'beach',
    'beach_club',
    'beauty_centre',
    'bed_breakfast',
    'boutique',
    'car_park',
    'city',
    'closest_airport_name',
    'club_lounge',
    'concierge',
    'couples_only',
    'day_spa',
    'family',
    'golf',
    'gym_fitness',
    'hair_salon',
    'health_programmes',
    'health_spa_resort',
    'heating',
    'hotel_apartment',
    'inhouse_movies',
    'in_room_spa_bath',
    'kids_club',
    'kitchen_facilities',
    'laundry_service',
    'lodge_safari',
    'lodge_ski',
    'mini_bar',
    'mountain_country',
    'night_club',
    'no_of_bars',
    'no_of_cafes',
    'no_of_restaurants',
    'plunge_pool',
    'prayer_room',
    'proximity_to_airport_kms',
    'proximity_to_city_centre_kms',
    'resort',
    'safe_deposit_box',
    'seaside',
    'shopping_mall',
    'smoking_rooms',
    'sound_system',
    'sports_club',
    'swimming_pool',
    'total_no_of_rooms',
    'tv_in_room',
    'valet_parking',
    'villas',
    'water_sports',
    'wheelchair_accessible',
    'wi_fi'
]

REDEEMBILITY_NOT_REDEEMABLE = "not_redeemable"
REDEEMABILITY_REDEEMABLE = "redeemable"
REDEEMABILITY_REDEEMABLE_REUSABLE = "redeemable_reusable"
REDEEMBILITY_REUSABLE = 'reusable'
REDEEMABILITY_NOT_REDEEMABLE = 'not_redeemable'
REDEEMABILITY_REDEEMED = 'redeemed'
REDEEMABILITY_REUSABLE = 'reusable'

QUERY_TYPE_NAME = 'name'

VALID_CATEGORIES = (
    CATEGORY_API_NAME_BODY,
    CATEGORY_API_NAME_LEISURE,
    CATEGORY_API_NAME_RESTAURANTS_AND_BARS,
    CATEGORY_API_NAME_RETAIL,
    CATEGORY_API_NAME_SERVICES,
    CATEGORY_API_NAME_TRAVEL
)
TYPE_MEMBER = 2
DEFAULT = 'default'
ALPHA = 'alpha'
HOTEL = 'hotel'
MALL = 'mall'

FEATURED_MERCHANT_ICON_URL_Body = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_body.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_Leisure = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_leisure.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_RestaurantsandBars = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_food.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_Retail = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_retail.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_Services = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_services.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_Travel = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_travel.png"  # noqa : E501
# please don't update constant name till here

FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_BODY = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_body_category_home_screen.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_LEISURE = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_leisure_category_home_screen.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_RESTAURANTS_AND_BARS = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_food_category_home_screen.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_RETAIL = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_retail_category_home_screen.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_SERVICES = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_services_category_home_screen.png"  # noqa : E501
FEATURED_MERCHANT_ICON_URL_CATEGORY_HOME_SCREEN_TRAVEL = "https://s3.amazonaws.com/entertainer-app-assets/categories/ribbons/cat_ribbon_travel.png"  # noqa : E501
LISTING_TYPE_ALL = 'all'
LISTING_TYPE_POINTS = 'points'
LISTING_TYPE_ET = 'et'

PUBLIC_CONFIGS = "public"
LOCATION_CONFIGS = ('id', 'name', 'currency')
INSTRUCTION_CONFIGS = ('text', 'url')
REFER_A_FRIEND_IMAGE = 'https://s3.amazonaws.com/entertainer-app-assets/refer_friend.jpg'
REFER_A_FRIEND_SHARE_LINK = 'https://entcartut.theentertainerme.com/products2020?et=1'

TIER_BRONZE = "bronze"
TIER_SILVER = "silver"
TIER_GOLD = "gold"
TIER_PLATINUM = "platinum"

TIER_NAME_BRONZE = "Bronze"
TIER_NAME_SILVER = "Silver"
TIER_NAME_GOLD = "Gold"
TIER_NAME_PLATINUM = "Platinum"
UPGRADE_TEXT = 'upgrade_text'

TIER_ID_SILVER = 2
TIER_ID_GOLD = 3

TIER_CONFIGS = {
    TIER_BRONZE: {
        "card_url": "https://app-home-tiles.s3.amazonaws.com/new_featured/Aldar/imgTierBronze%403x+(1).png",
        "range": 10000
    },
    TIER_SILVER: {
        "card_url": "https://app-home-tiles.s3.amazonaws.com/new_featured/Aldar/imgTierSilver%403x+(1).png",
        "range": 25000
    },
    TIER_GOLD: {
        "card_url": "https://app-home-tiles.s3.amazonaws.com/new_featured/Aldar/imgTierGold%403x+(1).png",
        "range": 9999999999
    },
    TIER_PLATINUM: {
        "card_url": "https://app-home-tiles.s3.amazonaws.com/new_featured/Aldar/imgTierPlatinum%403x+(1).png",
        "range": -1
    },
}

BURN_NOT_ENABLED_CODE = 871
INVALID_CONCEPT_ID_CODE = 870
NO_MAPPING_FOUND = 872

LMS_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
YAS_ISLAND_TITLE = "Yas Island"
EXPERIENCES_TITLE = "Experiences"

OTP_MSG = "Your pin to set your Aldar App is {otp}. Only valid for {expiry} mins."

EARN_TRANSACTIONS_KEY = "earn_transactions"
BURN_TRANSACTIONS_KEY = "burn_transactions"

TRANSACTION_TYPE_ACCRUAL = 'accrual'
TRANSACTION_TYPE_REDEMPTION = 'redemption'

TIER_BRONZE_BENEFITS = [
    {
        "name": "All",
        "benefits": []
    },
    {
        "name": "Hospitality",
        "benefits": [
            "30% Spa discount",
            "15% F&B discount"
        ]
    },
    {
        "name": "Education",
        "benefits": [
            "5 % discount on school trips and activities"
        ]
    },
    {
        "name": "Club House",
        "benefits": [
            "Community Gym Class Offers"
        ]
    },
    {
        "name": "Khidmah",
        "benefits": [
            "Avail 2 – hours maintenance package for ad-hoc jobs, and get 1hour free",
            "2 Months free on annual maintenance packages",
            "50 % off AC cleaning"
        ]
    },
    {
        "name": "Others",
        "benefits": [
            "Random prize draws (i.e. 2-night hotel stay)",
            "The ENTERTAINER vouchers depending on tier ( Aldar & the ENTERTAINER)",
            "Extra discount for Aldar Academy member ( per child)"
        ]
    },
    {
        "name": "Travel",
        "benefits": [
            "Convert points to Etihad Guest Miles - Coming Soon"
        ]
    }
]

TIER_SILVER_BENEFITS = [
    {
        "name": "All",
        "benefits": []
    },
    {
        "name": "Hospitality",
        "benefits": [
            "30% Spa discount",
            "15% F&B discount"
        ]
    },
    {
        "name": "Property",
        "benefits": [
            "Welcome basket on Handover of New Unit",
            "Professional photo of development invested in",
            "Pre – Launch access to new property developments",
            "Property Relationship Manager",
            "Preferred Payment Terms for Property Developments"
        ]
    },
    {
        "name": "Education",
        "benefits": [
            "5 % discount on school trips and activities"
        ]
    },
    {
        "name": "Club House",
        "benefits": [
            "Community Gym Class Offers"
        ]
    },
    {
        "name": "Khidmah",
        "benefits": [
            "2 Months free on annual maintenance packages",
            "50 % off AC cleaning",
            "Avail 2 – hours maintenance package for ad-hoc jobs, and get 1hour free"
        ]
    },
    {
        "name": "Others",
        "benefits": [
            "Random prize draws (i.e. 2-night hotel stay)",
            "The ENTERTAINER vouchers depending on tier ( Aldar & the ENTERTAINER)",
            "Extra discount for Aldar Academy member ( per child)"
        ]
    },
    {
        "name": "Travel",
        "benefits": [
            "Convert points to Etihad Guest Miles - Coming Soon"
        ]
    }
]

TIER_GOLD_BENEFITS = [
    {
        "name": "All",
        "benefits": []
    },
    {
        "name": "Hospitality",
        "benefits": [
            "Chefs Table exclusives at selected hotels",
            "30% Spa discount",
            "15% F&B discount",
            "Complimentary meal on Birthday at selected hotels",
            "Pool day pass (3 Per Year for 2 pax)",
            "1 Green fee at Golf Club",
            "1 Golf driving range"
        ]
    },
    {
        "name": "Property",
        "benefits": [
            "VIP classification for property developments",
            "Welcome basket on Handover of New Property",
            "VIP Property tours and presentations",
            "Rides to and from property developments",
            "Professional photo of property development invested in",
            "Pre – Launch access to new property developments",
            "Property Relationship Manager",
            "Preferred Payment Terms for Property Developments",
        ]
    },
    {
        "name": "Leasing ",
        "benefits": [
            "Free A/C cleaning (new leases only)"
        ]
    },
    {
        "name": "Education",
        "benefits": [
            "Personalised VIP school tours",
            "5 % discount on school trips and activities"
        ]
    },
    {
        "name": "Retail",
        "benefits": [
            "Akyasi - Home delivery",
            "Free Car washing"
        ]
    },
    {
        "name": "Club House",
        "benefits": [
            "Community Gym Class Offers"
        ]
    },
    {
        "name": "Khidmah",
        "benefits": [
            "2 Months free on annual maintenance packages",
            "50 % off AC cleaning",
            "Avail 2 – hours maintenance package for ad-hoc jobs, and get 1hour free"
        ]
    },
    {
        "name": "Others",
        "benefits": [
            "Random prize draws (i.e. 2-night hotel stay)",
            "The ENTERTAINER vouchers depending on tier (Aldar & the ENTERTAINER)",
            "Extra discount for Aldar Academy member ( per child)"
        ]
    },
    {
        "name": "Travel",
        "benefits": [
            "Convert points to Etihad Guest Miles - Coming Soon"
        ]
    }
]

TIER_PLATINUM_BENEFITS = [
    {
        "name": "All",
        "benefits": []
    },
    {
        "name": "Hospitality",
        "benefits": [
            "Chefs Table exclusives at selected hotels",
            "30% Spa discount",
            "15% F&B discount",
            "Complimentary meal on Birthday at selected hotels",
            "Pool day pass (3 Per Year for 2 pax)",
            "1 Green fee at Golf Club",
            "1 Golf driving range"
        ]
    },
    {
        "name": "Property",
        "benefits": [
            "VIP classification for property developments",
            "Welcome basket on Handover of New Property",
            "First option on new property releases",
            "5% discount on product launch",
            "VIP Property tours and presentations",
            "Personalized PM Manager and driver to collect documents/cheques",
            "Rides to and from property developments",
            "Professional photo of property development invested in",
            "Pre – Launch access to new property developments",
            "Property Relationship Manager",
            "Preferred Payment Terms for Property Developments"
        ]
    },
    {
        "name": "Leasing",
        "benefits": [
            "Free A/C cleaning  (new leases only)"
        ]
    },
    {
        "name": "Education",
        "benefits": [
            "Personalised VIP school tours",
            "5 % discount on school trips and activities"
        ]
    },
    {
        "name": "Retail",
        "benefits": [
            "Akyasi - Home delivery",
            "Free Valet Parking",
            "Free Car washing"
        ]
    },
    {
        "name": "Club House",
        "benefits": [
            "Community Gym Class Offers"
        ]
    },
    {
        "name": "Khidmah",
        "benefits": [
            "2 Months free on annual maintenance packages",
            "50 % off AC cleaning",
            "Avail 2 – hours maintenance package for ad-hoc jobs, and get 1hour free",
            "Free Annual Maintenance Service or Home sanitization"
        ]
    },
    {
        "name": "Others",
        "benefits": [
            "Random prize draws (i.e. 2-night hotel stay)",
            "The ENTERTAINER vouchers depending on tier ( Aldar & the ENTERTAINER)",
            "Extra discount for Aldar Academy member ( per child)"
        ]
    },
    {
        "name": "Travel",
        "benefits": [
            "Convert points to Etihad Guest Miles - Coming Soon"
        ]
    }
]

TIER_CATEGORY_BENEFITS = {
    'bronze': TIER_BRONZE_BENEFITS,
    'silver': TIER_SILVER_BENEFITS,
    'gold': TIER_GOLD_BENEFITS,
    'platinum': TIER_PLATINUM_BENEFITS
}
EARNED_DESCRIPTION = 'earned via app'
BURNED_DESCRIPTION = 'burned via app'

TIERS_LINK = {
    'silver': [TIER_BRONZE],
    'gold': [TIER_SILVER, TIER_BRONZE],
    'platinum': [TIER_GOLD, TIER_SILVER, TIER_BRONZE]
}

FILTER_SCOPE_CATEGORY = 'category'
FILTER_SCOPE_SUBCATEGORY = 'subcategory'
FILTER_SCOPE_ALL = 'all'

# Tier Upgrade Emails
USER_GROUP_CHANGE_TEMPLATES = {
    1: {
        'downgrade': current_app.config['SILVER_TO_BRONZE'],
    },
    2: {
        'downgrade': current_app.config['GOLD_TO_SILVER'],
        'upgrade': current_app.config['BRONZE_TO_SILVER']
    },
    3: {
        'downgrade': current_app.config['PLATINUM_TO_GOLD'],
        'upgrade': current_app.config['SILVER_TO_GOLD']
    },
    4: {
        'upgrade': current_app.config['GOLD_TO_PLATINUM']
    }
}

REFUND_DESCRIPTION = "{} refund call with LMS Wrapper Api"
REDEEM_POINTS_DESCRIPTION_ALDAR_API = "{} redeem points/amount call with aldar-api"

UPTO_TWO_DECIMALS = "{:.2f}"
LMS_SOURCE = 'aldar-api'
REDEEM_POINTS_DESCRIPTION = "{} redeem points/amount call with LMS Wrapper Api"

LINK_NOTIFICATION_X_DAYS_MSG = "Thank you for using your linked card, your points will reflect within {} days. "

BUSINESS_TRIGGERS_FOR_TAX_DEDUCTION = (
    'hospitality_fnb',
    'hospitality_golf_course',
    'hospitality_spa',
    'hospitality_sports_facilities'
)
