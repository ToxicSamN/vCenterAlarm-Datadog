
import logging
import json
import time, datetime
import os
import base64
import requests
import uuid
from .exceptions import *
from .encryption import AESCipher
from vcenterdd.log.setup import addClassLogger
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


logger = logging.getLogger(__name__)


@addClassLogger
class Datadog(object):

    def __init__(self, config_file):
        self.__api_key = None
        self.__application_key = None
        self.datadog_base_url = 'https://api.datadoghq.com/api/v1/'
        requests.adapters.DEFAULT_RETRIES = 3
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'Content-type': 'application/json'
        })
        self.proxies = None
        disable_warnings(InsecureRequestWarning)
        self.api_response = None
        self.config_file = config_file
        self.__cipher = AESCipher()

        self.setup_connection(config_file)

    def __get_api_key(self):
        return self.__decode_key(self.__api_key)

    def __store_api_key(self, api_key):
        self.__api_key = self.__encode_key(api_key)

    def __get_app_key(self):
        return self.__decode_key(self.__application_key)

    def __store_app_key(self, app_key):
        self.__application_key = self.__encode_key(app_key)

    def __encode_key(self, plaintxt):
        """
        This is purely obfuscation and not actually secure. but for the purposes for this project, this will do.
        :param string:
        :return: encoded string
        """
        return self.__cipher.encrypt(plaintxt)

    def __decode_key(self, enc_txt):
        return self.__cipher.decrypt(key=self.__cipher.AES_KEY, enc=enc_txt)

    def setup_connection(self, config_file):
        """
        Reads in the config file to get the API Key and App Key and and proxies that may be defined
        :param config_file:
        :return:
        """
        try:
            if not os.path.exists(config_file):
                raise FileExistsError('File path {} not found.'.format(config_file))
            self.config_file = config_file
            self.__log.info('Loading the Datadog config data')
            with open(config_file) as json_file:
                data = json.load(json_file)
                json_file.close()
            self.__log.debug(data.__str__())
            if data.get('api_key' or None):
                self.__store_api_key(data['api_key'])
            else:
                raise DatadogApiKeyError("Unable to locate Datadog API Key in file {}".format(config_file))

            if data.get('app_key' or None):
                self.__store_app_key(data['app_key'])

            if data.get('proxies' or None):
                self.proxies = data['proxies']

        except BaseException as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e

    def post_event(self, title, text, date_happened=datetime.datetime.now(), priority='normal', host='', tags=None,
                   alert_type='info', aggregation_key='', source_type_name='', related_event_id='',
                   device_name=''):
        """
        This method is matching that of the Datadog API documentation
        :param title: required parameter
        :param text: required parameter
        :param date_happened: required parameter, defaults to datetime.now()
        :param priority:
        :param host:
        :param tags:
        :param alert_type:
        :param aggregation_key:
        :param source_type_name:
        :param related_event_id:
        :param device_name:
        :return:
        """
        try:

            json_payload = {
                'title': "{}".format(title),
                'text': "{}".format(text),
                'date_happened': self._convert_to_epoch(date_happened),
            }
            if priority:
                json_payload.update({'priority': "{}".format(priority)})

            if host:
                json_payload.update({'host': "{}".format(host)})

            if tags:
                json_payload.update({'tags': tags})

            if alert_type:
                json_payload.update({'alert_type': "{}".format(alert_type)})

            if aggregation_key:
                json_payload.update({'aggregation_key': "{}".format(aggregation_key)})

            if source_type_name:
                json_payload.update({'source_type_name': "{}".format(source_type_name)})

            if related_event_id:
                json_payload.update({'related_event_id': related_event_id})

            if device_name:
                json_payload.update({'device_name': "{}".format(device_name)})

            url = "{}{}".format(self.datadog_base_url, 'events?api_key={}'.format(self.__get_api_key()))
            self.api_response = self.session.post(url=url, json=json_payload, timeout=1.0, proxies=self.proxies)
            self.validate_api_response()

        except BaseException as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e

    @staticmethod
    def _convert_to_epoch(date_time):
        if isinstance(date_time, datetime.datetime):
            return time.mktime(date_time.timetuple())

        raise TypeError("date_time parameter must be type 'datetime.datetime'")

    def post_metric(self, json_data):
        """
        Work in progress, not production ready
        :param json_data:
        :return:
        """
        try:
            if not self.validate_metric_json(json_data):
                raise ValueError("metric json_data must contain valid data. \n"
                                 "See documentation at https://docs.datadoghq.com/api/?lang=bash#post-timeseries-points")
            url = "{}{}".format(self.datadog_base_url, 'series?api_key={}'.format(self._get_api_key()))
            self.api_response = self.session.post(url=url, data=json_data)

            self.validate_api_response()

        except BaseException as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e

    def post_logs(self, method, data, tags=None):
        """
        Work in progress, not production ready
        :param method:
        :param data:
        :param tags:
        :return:
        """
        try:
            if method.lower() == 'post':
                url = "{}{}".format(self.datadog_base_url, 'input?api_key={}'.format(self._get_api_key()))
                self.api_response = self.session.get(url=url)

                self.validate_api_response()

        except BaseException as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e

    @staticmethod
    def validate_metric_json(self, json_data):
        if json_data.get('series' or None):
            series = json_data['series']
            # validate required parameters
            if series.get('metric' or None) and series.get('points' or None):
                if isinstance(series['points'], list):
                    # points should be a list of lists
                    for val in series['points']:
                        if not isinstance(val, list):
                            break

                    return True
        return False

    def validate_api_response(self):
        self.__log.info('Validating api response')
        self.__log.debug("HTTP Response: {}".format(self.api_response.status_code))
        try:
            self.api_response.raise_for_status()
            self.__log.info('API Response OK')
        except requests.exceptions.HTTPError as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e









