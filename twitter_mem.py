import redis
import json


class TwitterMemException(Exception):
	def __init__(self, error='', *args, **kwargs):
		self.error = error
		self.message = error
		super(Exception, self).__init__(error,  *args, **kwargs)


class TwitterMem:
	# Prefix argument is the name of application data which
	# is store in memory
	def __init__(self, prefix, host='localhost', port=6379):
		self.redis = redis.StrictRedis(host=host, port=port)
		self.prefix = prefix
		self.coordinates_prefix = '_'.join([self.prefix, 'coordinates'])


	# Saves to memory list of trends with key woeid.
	def save_trends(self, trends, woeid):
		data = self.redis.get(self.prefix)
		if data:
			data = json.loads(data)
			data[str(woeid)] = trends
		else:
			data = {str(woeid) : trends}
		self.redis.set(self.prefix, json.dumps(data))


	def save_coordinates(self, coordinates):
		self.redis.set(self.coordinates_prefix, json.dumps(coordinates))
		
		


		
