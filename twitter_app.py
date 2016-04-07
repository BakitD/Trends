import requests
import base64

from twitter_db import TwitterDBException
from requests import RequestException

#TODO include logging
#import logging


BEARER_TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'
TRENDS_PLACE_ENDPOINT = 'https://api.twitter.com/1.1/trends/place.json?'
TRENDS_AVAILABLE_ENDPOINT = 'https://api.twitter.com/1.1/trends/available.json'

TEST_WOEID = '23424757'


# Twitter base exception
class TwitterException(Exception):
	def __init__(self, *args, **kwargs):
		super(Exception, self).__init__(*args, **kwargs)

# Incorrect or bad requests. Raise this exception
# if only result of request to a twitter api
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
	# In case of successful issuing self.beaerer_token will be assigned.
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
	# If response status code is not 200 function generates
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
	# Otherwise returns response in json format.
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
	# This function could raise TwitterDBException or Error
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




	# TODO do main loop
	# TODO check rate limit error in twitter api
	# TODO check TwitterException class
	# TODO requests.codes.too_many is not fatal
	# TODO CREATE new function for available api
	# TEST TEST TEST TEST
	def run(self):
		try:
			# TODO add log after each function
			# TODO if self.db.open ? try to connect else close and raise fatal exception
			self.obtain_token()# not every time	
			places = self.get_trends_available()
			self.handle_trends_place(places)
		except RequestException as exc:
			print 'REQUEST EXCEPTION' # TODO log or stop ?
		except (AttributeError, KeyError, TypeError, ValueError) as error:
			print 'ERROR OCCURED', error.message# TODO what to do
		except TwitterBadResponse as exc:
			print 'BAD RESPONSE' # TODO Do something !
		except TwitterDBException as exc:
			print 'DB EXCEPTION'


		# MAIN LOOP TODO CONTINUE WITH TRENDS/PLACE
		#bearer_token = response.json()['access_token']




'''
result = make_test_request(bearer_token=bearer_token)
trends_list = result.json()[0]['trends']
for element in trends_list:
	print element['name'] + '\n', #'     volume: ', element['tweet_volume']
'''



