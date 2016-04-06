import requests
import base64

#TODO include logging and use RequestExceptions
#import logging
#from requests import RequestException

BEARER_TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'
TRENDS_PLACE_ENDPOINT = 'https://api.twitter.com/1.1/trends/place.json?'
TRENDS_AVAILABLE_ENDPOINT = 'https://api.twitter.com/1.1/trends/available.json'

TEST_WOEID = '23424757'


# Twitter base exception
class TwitterException(Exception): pass

# Incorrect or bad requests. Raise this exception
# if only result of request to a twitter api
# is not as it was supposed.
class TwitterBadResponse(TwitterException):
	def __init__(self, *args, **kwargs):
		self.code = None
		self.reason = None
		for key, value in kwargs.iteritems():
			if key == 'reason': self.reason = value
			if key == 'code': self.code = value
		super(TwitterException, self).__init__(*args, **kwargs)


class TwitterApp:
	def __init__(self, consumer_key, consumer_secret):
		self.bearer_token = None
		self.bearer_token_key = None
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
			raise TwitterBadResponse(reason=r.reason, code=r.status_code)
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
			raise TwitterBadResponse(reason=r.reason, code=r.status_code)
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
			raise TwitterBadResponse(reason=r.reason, code=r.status_code)
		return response.json()


	# TODO save to database
	# Handle trends/place result.
	def handle_trends_place(self, places):
		available_data = {}
		for element in places:
			if element['country'] in available_data:
				available_data[element['country']].append(element['name'])
			else:
				available_data[element['country']] = []

		f = open('available_locations.txt', 'w')
		for country, cities in available_data.iteritems():
			f.write(country.encode('utf-8'))
			for city in cities: f.write('\n\t' + city.encode('utf-8'))
			f.write('\n')

	#TODO continue main loop
	def run(self):
		self.obtain_token()		
		places = self.get_trends_available()
		self.handle_trends_place(places)


		# MAIN LOOP
		#bearer_token = response.json()['access_token']




'''
result = make_test_request(bearer_token=bearer_token)
trends_list = result.json()[0]['trends']
for element in trends_list:
	print element['name'] + '\n', #'     volume: ', element['tweet_volume']
'''



