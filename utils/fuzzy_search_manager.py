"""
Fuzzy search manager makes an API call that generates a response dict and it contains
 following classes:
 - FuzzySearchResponse
 - OutletScore
 - FuzzySearchManager
"""
import os
# TODO: No fuzzy search support for aldar so not installing elasticsaerch
# from elasticsearch import Elasticsearch
from flask import current_app
from requests import codes

# from app_configurations.settings import FUZZY_MANAGER_LOG_PATH
from common.api_utils import get_logger
# from common.constants import FUZZY_SEARCH_INDEX

__author__ = 'kamalh@theentertainerasia.com'


class FuzzySearchResponse(object):
    """
    FuzzySearchResponse contains some attributes which we want to return as part
     of our API call's response data
    """
    def __init__(self):
        self.fuzzy_response = None
        self.wildcard_response = None
        self.outlet_ids = []
        self.outlet_id_score = None
        self.outlet_ids_with_score = None
        self.all_scores = []
        self.is_valid_query = False
        self.is_succeeded = False
        self.is_timeout_or_server_down = False
        self.curl_status = 0
        self.total_results_found = 0
        self.total_unique_results_found = 0


class OutletScore(object):
    """
    OutletScore class contains some attributes related to OutletScore
    """
    def __init__(self):
        self.outlet_ids = []
        self.outlet_id_score = {}
        self.outlet_ids_with_score = []
        self.scores = []


class FuzzySearchManager(object):
    """
    FuzzySearchManager manages fuzzy searching, it has following methods:_
     - get_fuzzy_results
    """
    # def __init__(self):
    #     self.score_for_wildcard_search = 100
    #     self.elastic_search = Elasticsearch(current_app.config['ELASTIC_SEARCH_BASE_URL'])
    #     self.fm_logger = get_logger(
    #         filename=os.path.join(FUZZY_MANAGER_LOG_PATH, 'fuzzy_manager.log'),
    #         name=__class__.__name__
    #     )

    def get_fuzzy_results(self, query, category, sub_category, product_ids=None):
        """
        Get fuzzy results makes an API call to fuzzy_host and generates a
        FuzzySearchResponse accordingly and returns
        :param list product_ids: Product id
        :param str query: Fuzzy query
        :param str|None category:
        :param sub_category:
        :rtype: FuzzySearchResponse
        """
        response = FuzzySearchResponse()
        if not query:
            return response
        must_match, should_match = [], []
        minimum_should_match = 0
        search_in_fields = ['merchant_name', 'offer_name', 'outlet_name']
        must_match.append(
            {
                "multi_match": {
                    "query": "*{}*".format(query),
                    "fields": search_in_fields, "fuzziness": "AUTO"
                }
            }
        )

        if category and category.lower() != 'all':
            must_match_category = {'match': {'category': {'query': category}}}
            must_match.append(must_match_category)
        if product_ids and isinstance(product_ids, list):
            minimum_should_match = 1
            for product_id in product_ids:
                should_match.append({'match': {"product_id": int(product_id)}})
        if sub_category:
            must_match.append({'match': {'digital_section': {'query': sub_category}}})

        data = {
            "_source": ["outlet_id"],
            "size": 2000,
            "query": {
                "bool": {
                    "must": must_match,
                    "minimum_should_match": minimum_should_match,
                    "should": should_match
                }
            }
        }
        try:
            fuzzy_response = self.elastic_search.search(
                index=FUZZY_SEARCH_INDEX,
                timeout='{}s'.format(current_app.config['ELASTIC_SEARCH_MAX_SEC_FOR_TIMEOUT']),
                body=data

            )
            search_results_fuzzy = fuzzy_response.get('hits', {}).get('hits', [])
            if search_results_fuzzy:
                response.curl_status = codes.OK
                outlet_score = OutletScore()
                response.is_succeeded = True
                # response.fuzzy_response = search_results_fuzzy
                fuzzy_search_hits = fuzzy_response['hits']['total']
                if fuzzy_search_hits > 0:
                    response.total_results_found += fuzzy_search_hits
                    self.__process_search_results(search_results_fuzzy,
                                                  outlet_score, False)
                response.total_unique_results_found = len(outlet_score.outlet_ids)
                # Just for debugging
                response.outlet_ids = outlet_score.outlet_ids
                response.outlet_id_score = outlet_score.outlet_id_score
                response.outlet_ids_with_score = outlet_score.outlet_ids_with_score
                response.all_scores = list(set(outlet_score.scores))
                return response
        except Exception as e:
            self.fm_logger.exception("Error occurred while getting outlet ids from ES: {}".format(e))
        response.is_timeout_or_server_down = True
        return response

    def __process_search_results(self, search_response, outlet_score, is_wildcard_results=False):
        """
        Processes search results
        :param dict search_response: Search result
        :param OutletScore outlet_score: OutletScore object
        :param bool is_wildcard_results: FLag for wildcard
        :return:
        """
        for hit in search_response:
            outlet_id = hit['_source']['outlet_id']
            score = self.score_for_wildcard_search if is_wildcard_results else hit['_score']
            if outlet_score.outlet_id_score.get(outlet_id) is None:
                outlet_score.outlet_ids.append(outlet_id)
                outlet_score.outlet_id_score[outlet_id] = score
                outlet_score.scores.append(score)
                outlet_score.outlet_ids_with_score.append({
                    'outlet_id': outlet_id,
                    'relevance_score': score
                })
            else:  # override if new score is greater
                outlet_score_against_id = outlet_score.outlet_id_score.get(outlet_id)
                if outlet_score_against_id and score > outlet_score_against_id:
                    outlet_score.outlet_id_score[outlet_id] = score


fuzzy_search_manager = FuzzySearchManager()
