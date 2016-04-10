import requests
import base64
import schedule
import logging
import time
import re

from twitter_db import TwitterDBException
from requests import RequestException

BEARER_TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'
TRENDS_PLACE_ENDPOINT = 'https://api.twitter.com/1.1/trends/place.json?'
TRENDS_AVAILABLE_ENDPOINT = 'https://api.twitter.com/1.1/trends/available.json'
TWITTER_RSYMB = '[TZ]'

TEST_WOEID = '44418'

# Frequencies of requests

# Time between two trends requests.
# Twitter api set rate limit 15 requests per 15 minutes.
# Thus this application requests one trend every GET_TREND_SLEEP_TIME seconds.
TREND_REQUEST_SLEEP_TIME = 61

RE_BEARER_TOKEN = 25
RE_AVAILABLE = 25
RE_TRENDS = 25


# Twitter base exception
class TwitterException(Exception):
	def __init__(self, *args, **kwargs):
		super(Exception, self).__init__(*args, **kwargs)

# Incorrect or bad requests. Raise this exception
# if only the result of request to the twitter api
# is not as it was supposed.
class TwitterBadResponse(TwitterException):
	def __init__(self, reason, code, *args, **kwargs):
		self.code = code
		self.reason = reason
		super(TwitterException, self).__init__(*args, **kwargs)


class TwitterApp:
	def __init__(self, consumer_key, consumer_secret, db):
		self.bearer_token = None
		self.bearer_token_key = None
		self.db = db
		self.prepare_credentials(consumer_key, consumer_secret)


	def prepare_credentials(self, consumer_key, consumer_secret):
		concat_key = ':'.join([consumer_key, consumer_secret])
		concat_key = concat_key.encode('ascii')
		self.bearer_token_key = base64.urlsafe_b64encode(concat_key).decode('ascii')
		if not self.bearer_token_key:
			raise ValueError('Failure during preparing credentials')


	# Issuing bearer token. Function checks http response code.
	# If code doesn't equals 200 function generates exception.
	# In case of successful issuing self.bearer_token will be assigned.
	def obtain_token(self):
		headers = {
			'Authorization' : 'Basic %s' % self.bearer_token_key,
			'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8',
			'User-Agent' : 'My Twitter App v1.0.23',
			'Content-Length' : '29',
			'Accept-Encoding' : 'gzip',
		}
		data = 'grant_type=client_credentials'
		response = requests.post(BEARER_TOKEN_ENDPOINT, headers=headers, data=data)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		self.bearer_token = response.json()['access_token']


	# Function requests trends/available accordind to twitter api.
	# If the response status code is not 200 function generates
	# TwitterException otherwise returns result in json format.
	def get_trends_available(self):
		url = TRENDS_AVAILABLE_ENDPOINT
		headers = {
			'User-Agent' : 'My Twitter App v1.0.23',
			'Authorization' : 'Bearer %s' % self.bearer_token,
			'Accept-Encoding' : 'gzip',
		}
		response = requests.get(url, headers=headers)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		return response.json()


	# Function makes request to twitter trends/place api. If the result
	# of response is not http code 200 function generates exception.
	# Otherwise function returns response in json format.
	def get_trends_place(self, woeid):
		headers = {
			'User-Agent' : 'My Twitter App v1.0.23',
			'Authorization' : 'Bearer %s' % self.bearer_token,
			'Accept-Encoding' : 'gzip',
		}
		url = ''.join([TRENDS_PLACE_ENDPOINT, 'id=%s' % woeid])
		response = requests.get(url, headers=headers)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		return response.json()


	# Save available places to database.
	# This function may raise TwitterDBException or Error
	def handle_trends_place(self, places):
		countries = []
		cities = []
		for pl in places:
			if pl['placeType']['name'] == 'Country':
				countries.append({'name': pl['name'], \
						'woeid' : pl['woeid']})

			elif pl['placeType']['name'] == 'Town':
				cities.append({'name': pl['name'], \
						'woeid' : pl['woeid'], \
						'country' : pl['country']})
		self.db.add_country(countries)
		self.db.add_city(cities)


	# Handle the result of the trends/places requests.
	# This function may raise TwitterDBException or Error.
	def handle_trends(self, trends_data):
		trends_dict = trends_data[0]
		woeid = trends_dict['locations'][0]['woeid']
		datetime_nf = trends_dict['created_at']
		datetime = re.sub(TWITTER_RSYMB, ' ', datetime_nf)
		trends = trends_dict['trends']

		self.db.add_trends(trends, datetime, woeid)


	# Function obtains bearer token and if exception is
	# catched with bearer token hasn't been set, Exception will be
	# generated and the process will be stopped. Otherwise message
	# will be written to a log file. 
	def run_obtain_token(self):
		try:
			self.obtain_token()
		except (TwitterBadResponse, RequestException) as exc:
			if not self.bearer_token:
				raise Exception('RUN_OBTAIN_TOKEN: message=(%s, %s)' \
					% (exc.reason, exc.code))
			else:
				logging.error('RUN_OBTAIN_TOKEN: message=(%s, %s)' \
					% (exc.reason, exc.code))
		else:
			logging.info('RUN_OBTAIN_TOKEN: Task successfully finished.')


	# Function requests available places.
	def run_available(self):
		try:
			places = self.get_trends_available()
			self.handle_trends_place(places)
		except RequestException as exc:
			logging.error('RUN_AVAILABLE: message=(%s)' % exc.message)
		except (AttributeError, KeyError, TypeError, ValueError) as error:
			logging.error('RUN_AVAILABLE: message=(%s)' % error.message)
		except TwitterBadResponse as exc:
			logging.error('RUN_AVAILABLE: message=(%s, %s)' \
					%(exc.reason, exc.code))
		except TwitterDBException as exc:
			logging.error('RUN_AVAILABLE: message=(%s)' % exc.message)
		else:
			logging.info('RUN_AVAILABLE: Task successfully finished.')


	# This function requests every TREND_REQUEST_SLEEP_TIME seconds
	# trends for specific city and saves it to database.
	# TODO Make queueing to choose city USE REDIS
	def run_trends(self):
		try:
			countries, cities = self.db.get_places()
			for city in cities:
				trends_data = self.get_trends_place(city['woeid'])
				self.handle_trends(trends_data)
				logging.info('RUN_TRENDS: Trends for %s city with woeid = %s \
					woeid has been saved.' % (city['name'], city['woeid']))
				time.sleep(TREND_REQUEST_SLEEP_TIME)
		except RequestException as exc:
			logging.error('RUN_TRENDS: message=(%s)' % exc.message)
		except (AttributeError, KeyError, TypeError, ValueError) as error:
			logging.error('RUN_TRENDS: message=(%s)' % error.message)
		except TwitterBadResponse as exc:
			logging.error('RUN_TRENDS: message=(%s, %s)' \
					%(exc.reason, exc.code))
		except TwitterDBException as exc:
			logging.erro('RUN_TRENDS: message=(%s)' % exc.message)
		else:
			logging.info('RUN_TRENDS: Task successfully finished.')


	def run(self):
		self.obtain_token()
		self.run_trends()


	# Function set schedule for tasks
	# TODO set frequency of tasks
	# TODO change algorithm if error is occured
	# TODO start new cycle at specific time not after some
	def run_temp(self):

		# MAIN LOOP TODO CONTINUE WITH TRENDS/PLACE
		schedule.every(0.25).minutes.do(self.run_obtain_token)
		schedule.every(0.25).minutes.do(self.run_available)
		logging.info('Starting tasks ...')

		while True:
			schedule.run_pending()
			time.sleep(5)
			print '*'


