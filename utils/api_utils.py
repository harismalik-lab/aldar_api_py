"""
API Utils reside here
"""
import json
import random
import string

from _operator import itemgetter
from datetime import timedelta, datetime
from functools import cmp_to_key
from random import randint

import requests
from flask import g, current_app

from common.constants import EN, SUPPORTED_LOCALES, CATEGORY_API_NAME_RESTAURANTS_AND_BARS, CATEGORY_API_NAME_TRAVEL, \
    CATEGORY_API_NAME_BODY, CATEGORY_API_NAME_LEISURE, CATEGORY_API_NAME_RETAIL, CATEGORY_API_NAME_SERVICES, \
    FEATURED_MERCHANT_ICON_URL_Body, FEATURED_MERCHANT_ICON_URL_Leisure, FEATURED_MERCHANT_ICON_URL_RestaurantsandBars, \
    FEATURED_MERCHANT_ICON_URL_Retail, FEATURED_MERCHANT_ICON_URL_Services, FEATURED_MERCHANT_ICON_URL_Travel, AED, \
    TIER_CONFIGS, TIER_BRONZE, OTP_MSG, OTP_EXPIRATION_IN_MINUTES
from models.aldar_app.users_password_history import UsersPasswordHistory
from models.entertainer_web.home_screen_configurations import HomeScreenConfiguration
from models.entertainer_web.home_screen_configurations_section import HomeScreenConfigurationsSection
from models.entertainer_web.offer_wl_active import OfferWlActive
from models.entertainer_web.redemption import Redemption
from models.entertainer_web.wl_tabs import WlTab
from utils.global_sms import global_sms
from utils.lms_manager import lms_manager
from utils.security import security

cache = g.cache


@cache.memoize(timeout=1800)
def get_home_screen_conf(location_id, user_group=0, company='', locale=EN):
    """
    Gets all home screen configurations section
    :param  int location_id: user location id
    :param  int user_group:  user group
    :param  str company:     user company
    :param  str locale:      user language
    """
    count = 0
    result = HomeScreenConfigurationsSection.get_all(location_id, user_group, company, locale)
    if not result and count == 0:
        count += 1
        result = HomeScreenConfigurationsSection.get_all(location_id=0, user_group=0, company=company, locale=locale)
    return result


@cache.memoize(timeout=1800)
def get_home_screen_tiles(locale, location_id, company, user_group):
    """
    Home screen tiles

    :param locale: Locale
    :param location_id: id of location
    :param company: company
    :param user_group: user group
    :return:
    """
    tiles = HomeScreenConfiguration.get_all_sections(
        locale=locale,
        location_id=location_id,
        company=company,
        user_group=user_group
    )
    return tiles


def tabs_param_parser(param):
    """
    Checks if param is in bool params list then return bool value otherwise returns the param
    :param param:
    :return:
    """
    if param in ('True', 'true', True, 1, '1'):
        return True
    if param in ('False', 'false', False, 0, '0'):
        return False
    return param


@cache.memoize(timeout=1800)
def get_tabs_cached(company, locale):
    """
    Gets tabs from db prepares a response dict
    :param company:
    :param locale:
    :return:
    """
    tabs = WlTab.get_by_company_and_locale(company, locale)
    tabs_list = []
    for tab in tabs:
        params = dict()
        params_list = []
        params_array = tab.params.split(',') if tab.params else []
        for param_array in params_array:
            param = param_array.split("=")
            if len(param):
                param[1] = tabs_param_parser(param[1])
                params[param[0]] = param[1]
                params_list.append({'key': param[0], 'value': param[1]})
        tabs_list.append({
            'section_type': tab.type_id,
            'order': tab.order,
            'uid': tab.type,
            'name': tab.name,
            'params': params,
            'params_list': params_list
        })
    return tabs_list


def get_locale(locale):
    """
    Returns valid locale
    :param str locale: passed locale
    :rtype: str
    """
    if locale in SUPPORTED_LOCALES:
        return locale
    return EN


def get_configured_sku_by_company(company):
    company = company.lower()
    skus = {}
    return skus.get(company, [])


def user_redemptions_lookup_hash(customer_id, company, offer_ids):
    """
    Returns user redemptions lookup hash
    :rtype: dict
    """
    user_redemptions = Redemption.get_by_customer_id_and_company(customer_id, company, offer_ids)
    redemption_quantities = {}
    for redemption in user_redemptions:
        index = "{}_{}".format(redemption.offer_id, redemption.product_id)
        if not redemption_quantities.get(index):
            redemption_quantities[index] = redemption.quantity
        else:
            redemption_quantities[index] = redemption_quantities.get(index) + redemption.quantity
    return redemption_quantities


def calculate_redeemability(offer, customer_product_ids, redemption_quantities, date_from, date_to):
    """
    Calculates if an offer is redeemable or not and returns it's redeemability dict
    :param datetime.datetime date_to: Offer expiration date
    :param datetime.datetime date_from: Offer validation date
    :param dict redemption_quantities: Customer redemption hash
    :param list customer_product_ids: Customer purchased product ids
    :param OfferWlActive offer: Offer
    """
    is_redeemable = False
    num_purchased = 0
    num_redemptions = 0
    is_offer_valid_in_future = False
    is_offer_expired = False
    allowed_onboarding = False
    is_purchased = int(offer.product_id) in customer_product_ids

    if redemption_quantities:
        check = "{}_{}".format(offer.id, offer.product_id)
        if redemption_quantities.get(check):
            num_redemptions = redemption_quantities.get(check)
        else:
            num_redemptions = 0

    if offer.valid_from_date > date_from:
        is_offer_valid_in_future = True

    if offer.expiration_date < date_to:
        is_offer_expired = True

    num_purchased += int((customer_product_ids.count(int(offer.product_id or 0)) * int(offer.quantity or 0)))

    if offer.type == OfferWlActive.TYPE_MEMBER and is_purchased:
        num_purchased = int(num_redemptions) + 1

    if (
            not is_offer_valid_in_future and
            not is_offer_expired and
            int(num_purchased) > int(num_redemptions) and
            int(num_purchased) > 0
    ):
        is_redeemable = True
        if offer.type == OfferWlActive.TYPE_DEFAULT:
            redeemability_value = Redemption.REDEEMABLE
        else:
            redeemability_value = Redemption.REUSABLE

    elif int(num_redemptions) >= int(num_purchased) > 0:
        redeemability_value = Redemption.REDEEMED
    else:
        redeemability_value = Redemption.NOT_REDEEMABLE

    is_show_purchase_button = False

    return {
        'is_redeemable': is_redeemable,
        'redeemability': redeemability_value,
        'is_purchased': is_purchased,
        'is_offer_valid_in_future': is_offer_valid_in_future,
        'is_offer_expired': is_offer_expired,
        'quantity_redeemable': offer.quantity if redeemability_value == Redemption.REUSABLE else
        max(0, int(num_purchased) - int(num_redemptions)),
        'quantity_redeemed': 0 if redeemability_value == Redemption.REUSABLE else num_redemptions,
        'quantity_not_redeemable': offer.quantity if not is_purchased and not allowed_onboarding else 0,
        'is_show_purchase_button': is_show_purchase_button
    }


def is_search_string_found(search_in, search_string, is_search_words=False):
    """
    Search the presence of word in string.
    :param str search_in: string in which need to search
    :param str search_string: string to find
    :param bool is_search_words: let us know that search string is single word or combination of words
    :rtype: bool
    """
    search_string = search_string.strip().lower()
    if not is_search_words:
        return search_string in search_in
    else:
        search_words = search_string.split()
        # if search_in i.e offer_name is None then set it to empty string so that code doesn't break
        if not search_in:
            search_in = ''
        for word in search_words:
            if word.strip() and word.strip() not in search_in.lower():
                return False
        return True


def compare(a, b):
    """
    Compare 2 values
    """
    try:
        return (a > b) - (a < b)
    except TypeError:
        return -1


def multi_key_sort(items, columns, functions=None, getter=itemgetter):
    """
    Sort a list of dictionary objects or objects by multiple keys bidirectionally.
    Keyword Arguments:
    items -- A list of dictionary objects or objects
    columns -- A list of column names to sort by. Use -column to sort in descending order
    functions -- A Dictionary of Column Name -> Functions to normalize or process each column value
    getter -- Default "getter" if column function does not exist
              operator.itemgetter for Dictionaries
              operator.attrgetter for Objects
    usage: https://gist.github.com/malero/418204
    """
    if functions is None:
        functions = {}
    comparers = []
    for column in columns:
        column = column[1:] if column.startswith('-') else column
        if column not in functions:
            functions[column] = getter(column)
        comparers.append((functions[column], 1 if column == column else -1))

    def comparer(left, right):
        for func, polarity in comparers:
            result = compare(func(left), func(right))
            if result:
                return polarity * result
        else:
            return 0

    return sorted(items, key=cmp_to_key(comparer))


def get_category_badge(category, categories, selected_category):
    """
    Gets category badge
    """
    for cat in categories:
        if category == cat['api_name'] and selected_category != cat['api_name']:
            return cat['image']
    return ''


def get_featured_ribbon_image(category):
    """
    Gets featured ribbon image
    """
    if category:
        if category == CATEGORY_API_NAME_BODY:
            return FEATURED_MERCHANT_ICON_URL_Body
        elif category == CATEGORY_API_NAME_LEISURE:
            return FEATURED_MERCHANT_ICON_URL_Leisure
        elif category == CATEGORY_API_NAME_RESTAURANTS_AND_BARS:
            return FEATURED_MERCHANT_ICON_URL_RestaurantsandBars
        elif category == CATEGORY_API_NAME_RETAIL:
            return FEATURED_MERCHANT_ICON_URL_Retail
        elif category == CATEGORY_API_NAME_SERVICES:
            return FEATURED_MERCHANT_ICON_URL_Services
        elif category == CATEGORY_API_NAME_TRAVEL:
            return FEATURED_MERCHANT_ICON_URL_Travel
    else:
        return ''


def set_images_and_attributes(company, outlet, categories, selected_category=''):
    """
    Sets images and attributes
    """
    outlet['attributes'] = []

    # if outlet.get('is_new'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_new.png'
    #     })
    #
    # if outlet.get('is_monthly'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_monthly.png'
    #     })
    #
    # if outlet.get('is_cheers'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_cheers.png'
    #     })
    #
    # if outlet.get('is_delivery'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_delivery.png'
    #     })
    #
    # if outlet.get('is_more_sa'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_more_sa.png'
    #     })
    #
    # if outlet.get('is_shared'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': 'https://s3.amazonaws.com/entertainer-app-assets/icons/badge_pinged.png'
    #     })

    # if not outlet.get('is_featured'):
    #     for category in outlet['categories']:
    #         if category != selected_category:
    #             outlet['attributes'].append({
    #                 'type': 'image',
    #                 'value': get_category_badge(category, categories, selected_category)
    #             })
    #         if category == CATEGORY_API_NAME_RESTAURANTS_AND_BARS:
    #             for cuisine in outlet['merchant']['cuisines']:
    #                 outlet['attributes'].append({
    #                     'type': 'text',
    #                     'value': cuisine
    #                 })
    #
    #         if category == CATEGORY_API_NAME_TRAVEL:
    #             # we have list in outlet['sub_categories'] and we need to get index against specific category
    #             category_index = [index for index, value in enumerate(outlet['sub_categories']) if value == category]
    #             if category_index:
    #                 outlet['attributes'].append({
    #                     'type': 'image',
    #                     'value': outlet['sub_categories'][category_index[0]]
    #                 })
    #
    # if outlet.get('is_featured'):
    #     outlet['attributes'].append({
    #         'type': 'image',
    #         'value': get_featured_ribbon_image(outlet['category']),
    #         'is_featured': True
    #     })

    if not outlet.get('is_redeemable'):
        if outlet.get('is_purchased'):
            outlet['locked_image_url'] = 'https://s3.amazonaws.com/entertainer-app-assets/icons/locked_outlet_golden.png'  # noqa: E501
        else:
            outlet['locked_image_url'] = 'https://s3.amazonaws.com/entertainer-app-assets/icons/locked_outlet_grey.png'  # noqa: E501


def get_user_tier_dict(lms_member_id):
    """
    Gets user tier information dictionary
    :param str lms_member_id: lms member id
    :return dict: user_tier_dict
    """
    lms_profile_dict = lms_manager.get_lms_user_profile(lms_member_id)
    user_tier_dict = {
        "current_balance": lms_profile_dict['total_available_points'],
        "card_id": lms_profile_dict['mobile_number'],
        "current_tier": lms_profile_dict['member_tier'],
        "amount_spent": lms_profile_dict['used_points'],
        "tier_range": lms_profile_dict['used_points'],
        "currency": AED,
    }
    tier_config = TIER_CONFIGS.get(lms_profile_dict['member_tier'].lower(), TIER_CONFIGS[TIER_BRONZE])
    user_tier_dict['tier_image'] = tier_config.get('card_url')
    user_tier_dict['tier_range'] = tier_config.get('range')

    return user_tier_dict


def is_password_previously_used(new_password, aldar_user_id):
    """
    Validates new password is in last 2 recent passwords changed by user or not
    :param str new_password: new password of user
    :param int aldar_user_id: user id of user
    :return:
    """
    user_passwords_history = UsersPasswordHistory.get_password_history_by_id(aldar_user_id)
    if user_passwords_history:
        for record in user_passwords_history:
            if security.validate_password(new_password, record.password) or \
                    security.validate_hash_magento(new_password, record.password):
                # new password matches last 2 used password
                return True
    return False


def get_iso_formatted_date(date_obj):
    """
    convert datetime object to iso formatted date str
    :param date_obj: datetime object
    :return: str
    """
    date_obj = date_obj - timedelta(hours=4)
    return "{}+04:00".format(date_obj.isoformat())


def send_sms_to_user(otp, msisdn):
    """
    send otp msg to user via Synapse
    """
    otp_msg = OTP_MSG.format(otp=otp, expiry=OTP_EXPIRATION_IN_MINUTES)
    global_sms.send_sms(mobile_number=msisdn, message=otp_msg)


def get_braze_android_message_object(message, transaction_id, notification=False):
    """
    Creates android object for braze push notification
    :param notification:
    :param transaction_id:
    :param message:
    :return:
    """
    android_msg_object = {
        "alert": message,
        "custom_uri": "adrentertainer://clotransaction?trans_id={}".format(transaction_id),
        "push_icon_image_url": "https://www.darnarewards.com/images/hdr-logo.png",
        "send_to_most_recent_device_only": True
    }
    if notification:
        del android_msg_object['custom_uri']
    return android_msg_object


def get_braze_apple_message_object(message, transaction_id, notification=False):
    """
    Creates apple object for braze push notification
    :param notification:
    :param transaction_id:
    :param message:
    :return:
    """
    apple_msg_object = {
        "alert": message,
        "custom_uri": "adrentertainer://clotransaction?trans_id={}".format(transaction_id),
        "push_icon_image_url": "https://www.darnarewards.com/images/hdr-logo.png",
        "send_to_most_recent_device_only": True
    }
    if notification:
        del apple_msg_object['custom_uri']
    return apple_msg_object


def push_braze_notification(external_user_id, android_message_obj, apple_message_obj):
    """
    This will push app notification in case of a transaction is received
    :param external_user_id: Braze user id
    :param android_message_obj: Android message object
    :param apple_message_obj: Apple message object
    """
    payload = {
        "external_user_ids": [external_user_id],
        "messages": {
            "android_push": android_message_obj,
            "apple_push": apple_message_obj
        }
    }
    headers = {
        'Authorization': "Bearer {}".format(current_app.config['BRAZE_AUTH_TOKEN']),
        'Content-Type': 'application/json'
    }

    response = requests.post(
        current_app.config['BRAZE_SEND_MESSAGE_API'],
        headers=headers,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return response.json()


def generate_transaction_id(concept_id):
    """
    returns a str consists of concept_id, time_stamp, 4 random digits
    """
    return '{}-{}-{}'.format(concept_id, datetime.now().strftime("%s"), randint(1000, 9999))


def generate_random_string(length=32):
    """
    Generates random string
    :param length: length of the string
    :return:
    """
    random_string = string.ascii_letters + string.digits
    return ''.join((random.choice(random_string)) for x in range(length))
