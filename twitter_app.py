import requests
import base64
import logging
import time
import re
import ConfigParser

from datetime import datetime, timedelta
from requests import RequestException
from twitter_db import TwitterDBException
from twitter_mem import TwitterMemException
from settings import TREND_NUM_PER_PLACE, DATETIME_FORMAT, YAHOO_APP_ID#, GOOGLE_APP_ID



# Twitter endpoints
BEARER_TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'
TRENDS_PLACE_ENDPOINT = 'https://api.twitter.com/1.1/trends/place.json?'
TRENDS_AVAILABLE_ENDPOINT = 'https://api.twitter.com/1.1/trends/available.json'


# Too many requests constant
TOO_MANY = requests.codes.too_many or 429

# Test value
TEST_WOEID = '44418'

# Time between two trends requests.
# Twitter api has rate limit 15 requests per 15 minutes.
TREND_REQUEST_SLEEP_TIME = 61

# Update time period in hours.
# This constant is used to define when to update trends
TREND_UPDATE_TIME = 24

# Time interval between task launch time in hours
TASK_INTERVAL = 24

# Time to wait if too_many error occured in minutes
TOO_MANY_WAIT = 15

# Sleep time in seconds
SLEEP_TIME = 900

# Delay before first start in seconds
START_DELAY = 5

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
	def __init__(self, config_filename, db, memdb):
		self.config_filename = config_filename
		self.tokens = []
		self.db = db
		self.memdb = memdb



	# Read configuration file.
	def read_config(self):
		config = ConfigParser.ConfigParser()
		config.read(self.config_filename)
		credentials = {}
		for section in config.sections():
			credentials[section] = {
				'consumer_key' : \
					config.get(section, 'consumer_key'),
				'consumer_secret' : \
					config.get(section, 'consumer_secret')
			}
		return credentials


	# Encodes consumer key and consumer secret keys.
	def encode(self, consumer_key, consumer_secret):
		concat_key = ':'.join([consumer_key, consumer_secret])
		concat_key = concat_key.encode('ascii')
		return base64.urlsafe_b64encode(concat_key).decode('ascii')


	# Issuing bearer token. Function checks http response code.
	# If code doesn't equals 200 function generates exception.
	# In case of successful bearer_token will be returned.
	def obtain_bearer_token(self, consumer_key, consumer_secret):
		headers = {
			'Authorization' : 'Basic %s' % \
				self.encode(consumer_key, consumer_secret),
			'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8',
			'User-Agent' : 'My Twitter App v1.0.23',
			'Content-Length' : '29',
			'Accept-Encoding' : 'gzip',
		}
		data = 'grant_type=client_credentials'
		response = requests.post(BEARER_TOKEN_ENDPOINT, headers=headers, data=data)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		return response.json()['access_token']


	# Obtaining tokens for every key in argument credentials.
	def obtain_tokens(self, credentials):
		tokens = []
		for key, data in credentials.iteritems():
			tokens.append(self.obtain_bearer_token( \
				data['consumer_key'], data['consumer_secret']))
		return tokens


	# Function reads configuration file and obtains bearer tokens.
	def set_tokens(self):
		try:
			tokens = self.obtain_tokens(self.read_config())
		except ConfigParser.Error as error:
			logging.critical('SET_TOKEN: Critical error during '
						'reading config file!')
			raise Exception(error)
		except (TwitterBadResponse, RequestException) as exc:
			if not self.tokens:
				raise Exception('SET_TOKEN: message=(%s, %s)' \
					% (exc.reason, exc.code))
			else:
				logging.error('SET_TOKEN: Tokens have not been obtained. '
						'Old tokens will be used. Message=(%s)' % exc)
		else:
			self.tokens[:] = []
			self.tokens = tokens
			logging.info('SET_TOKEN: Tokens have been successfully obtained!')


	# Defines the token choice algorithm.
	def token_choice(self):
		return self.tokens[0]


	# Function requests trends/available accordind to twitter api.
	# If the response status code is not 200 function generates
	# TwitterException otherwise returns result in json format.
	def get_trends_available(self):
		url = TRENDS_AVAILABLE_ENDPOINT
		headers = {
			'User-Agent' : 'My Twitter App v1.0.23',
			'Authorization' : 'Bearer %s' % self.token_choice(),
			'Accept-Encoding' : 'gzip',
		}
		response = requests.get(url, headers=headers)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		return response.json()


	# Function makes request to twitter trends/place api. If the result
	# of response is not http code 200 function generates exception.
	# Otherwise function returns response in json format.
	def get_trends_place(self, bearer_token, woeid):
		headers = {
			'User-Agent' : 'My Twitter App v1.0.23',
			'Authorization' : 'Bearer %s' % bearer_token,
			'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8',
			'Accept-Encoding' : 'gzip',
		}
		url = ''.join([TRENDS_PLACE_ENDPOINT, 'id=%s' % woeid])
		response = requests.get(url, headers=headers)
		if response.status_code != requests.codes.ok: 
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		return response.json()

	# Get longitude and latitude using yahoo api
	def get_coordinates(self, url):
		url += '?' + '&'.join(['appid=' + YAHOO_APP_ID, 'format=json'])
		response = requests.get(url)
		if response.status_code != requests.codes.ok:
			raise TwitterBadResponse(reason=response.reason, code=response.status_code)
		result = response.json()
		longitude = result['place']['centroid']['longitude']
		latitude = result['place']['centroid']['latitude']
		return longitude, latitude

	# Translate places names
	'''
	def translate_place_name(self, places):
		for place in places:
			url = 'https://www.googleapis.com/language/translate/v2/detect?key=' + GOOGLE_APP_ID \
				+ '&q=' + place['name']
			print url
			import sys
			sys.exit()
			response = requests.get(url)
			if response.status_code != requests.codes.ok:
				raise TwitterBadResponse(reason=response.reason, code=response.status_code)
			result = response.json()
			print result
		import sys
		sys.exit()
	'''

	# Save available places to database.
	# This function may raise TwitterDBException or Error
	def handle_trends_place(self, places):
		woeid_list = self.db.get_woeids()
		places_list = []	
		for pl in places:
			if unicode(pl['woeid']) in woeid_list: continue
			placetype = pl['placeType']['name']
			if placetype == 'Country' : placetype = 'country'
			elif placetype == 'Supername': placetype = 'worldwide'
			elif placetype == 'Town': placetype = 'town'
			else:
				logging.info('HANDLE_TRENDS_PLACES: New placeType is detected: %s!' % placetype)
				continue
			longitude, latitude = self.get_coordinates(pl['url'])
			places_list.append({'name': pl['name'],	'woeid' : pl['woeid'], \
						'parent_id' : pl['parentid'], \
						'placetype' : placetype, \
						'longitude' : longitude, \
						'latitude' : latitude})
		dtime = (datetime.now() - timedelta(days=1)).strftime(DATETIME_FORMAT)
		self.db.add_places(places_list,dtime)
		logging.info('HANDLE_TRENDS_PLACE: Total: database:%s, request:%s, added:%s' \
					% (len(woeid_list), len(places), len(places_list)))

	# Function requests available places.
	def run_available(self):
		status = False
		try:
			self.handle_trends_place(self.get_trends_available())
		except RequestException as exc:
			logging.error('RUN_AVAILABLE: message=(%s)' % exc.message)
		except (AttributeError, KeyError, TypeError, ValueError) as error:
			logging.error('RUN_AVAILABLE: message=(%s)' % error.message)
		except TwitterBadResponse as exc:
			logging.error('RUN_AVAILABLE: message=(%s, %s)' \
					%(exc.reason, exc.code))
			if exc.code == TOO_MANY: status = TOO_MANY
		except TwitterDBException as exc:
			logging.error('RUN_AVAILABLE: message=(%s)' % exc.message)
		else:
			logging.info('RUN_AVAILABLE: Task successfully finished.')
			status = True
		return status

	# Prepare trends
	def prepare_trends(self, trends):
		def sort_method(value):
			try: result = int(value.get('tweet_volume'))
			except: result = 0
			return result
		return sorted(trends, key=sort_method, reverse=True)[:TREND_NUM_PER_PLACE]


	# Handle the result of the trends/places request.
	# This function may raise TwitterDBException or Error.
	def handle_trends(self, trends_data, longitude, latitude):
		trends_dict = trends_data[0]
		woeid = trends_dict['locations'][0]['woeid']
		trends = trends_dict['trends']
		self.db.add_trends(trends, woeid)
		self.memdb.save_trends(self.prepare_trends(trends), woeid, longitude, latitude)



	# This function saves trends to database.
	def get_and_save_trends(self, place, bearer_token):
		trends = self.get_trends_place(bearer_token, place['woeid'])
		self.handle_trends(trends, place['longitude'], place['latitude'])
		logging.info('RUN_TRENDS: Trends for %s which woeid is %s ' 
			'has been saved.' % (place['name'], place['woeid']))



	# This function takes one city from cities list for which trends have been updated
	# update_time days ago and for every city in cities list
	# using possible tokens requests trends. Then wait for some time.
	def run_trends_algorithm(self, update_time):
		places = self.db.get_places(update_time)
		flag = True
		while flag:
			for token in self.tokens:
				if places: 
					self.get_and_save_trends(places.pop(0), token)
				else: break
			if not places: flag = False
			else: time.sleep(TREND_REQUEST_SLEEP_TIME)



	def run_trends(self, update_time):
		status = False
		try:
			self.run_trends_algorithm(update_time)
		except RequestException as exc:
			logging.error('RUN_TRENDS: message=(%s)' % exc.message)
		except (AttributeError, KeyError, TypeError, ValueError) as error:
			logging.error('RUN_TRENDS: message=(%s)' % error.message)
		except TwitterBadResponse as exc:
			logging.error('RUN_TRENDS: message=(%s, %s)' \
					%(exc.reason, exc.code))
			if exc.code == TOO_MANY: status = TOO_MANY
		except TwitterDBException as exc:
			logging.error('RUN_TRENDS: message=(%s)' % exc.message)
		except TwitterMemException as exc:
			logging.error('RUN_TRENDS: message=(%s)' % exc.message)
		else:
			logging.info('RUN_TRENDS: Task successfully finished.')
			status = True
		return status


	# Start all tasks
	def run_tasks(self):
		logging.info('Starting tasks')
		self.set_tokens()
		available_status = self.run_available()
		trends_status = self.run_trends(TREND_UPDATE_TIME)
		if not available_status and not trends_status:
			raise Exception('Unexpected exception occured!')
		return available_status, trends_status
		


	# Schedule
	def schedule(self):
		start_time = datetime.now()
		while True:
			if datetime.now() >= start_time:
				available_status, trends_status = self.run_tasks()
				if TOO_MANY in (available_status, trends_status):
					start_time = datetime.now() + timedelta(minutes=TOO_MANY_WAIT)
				else:
					start_time = datetime.now() + timedelta(hours=TASK_INTERVAL)
				logging.info('Tasks were executed. Next start at %s' \
						% start_time.strftime(DATETIME_FORMAT))
			time.sleep(SLEEP_TIME)


	def run(self):
		self.schedule()
