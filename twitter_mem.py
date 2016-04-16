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


	# Saves to memory list of trends with key woeid.
	def save_trends(self, trends, woeid):
		trend_list = []
		for element in trends:
			trend_list.append(element['name'])
		data = self.redis.get(self.prefix)
		if data:
			data = json.loads(data)
			data[str(woeid)]['trends'] = trend_list
		else:
			data = {}
			data[str(woeid)] = {'trends' : trend_list, 'coordinates':{}}
		self.redis.set(self.prefix, json.dumps(data))


	def save_coordinates(self, coordinates):
		data = self.redis.get(self.prefix)
		if data:
			data = json.loads(data)
			for woeid, coord in coordinates.iteritems():
				data[str(woeid)]['coordinates'] = coord
		else:
			data = {}
			for woeid, coord in coordinates.iteritems():
				data[str(woeid)] = {'trends' : [], 'coordinates':coord}
		self.redis.set(self.prefix, json.dumps(data))


