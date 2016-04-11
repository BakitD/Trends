import MySQLdb as mysql
import base64
from contextlib import closing
from settings import DATETIME_FORMAT

class TwitterDBException(Exception):
	def __init__(self, error='', *args, **kwargs):
		self.error = error
		self.message = error
		super(Exception, self).__init__(error,  *args, **kwargs)


class TwitterDB:
	def __init__(self, user, password, dbname, host='localhost'):
		self.db = None
		self.user = user
		self.host = host
		self.password = base64.b64encode(password)
		self.dbname = dbname

	def connect(self):
		try:
			self.db = mysql.connect( \
				host=self.host, user=self.user, \
				passwd=base64.b64decode(self.password), \
				db=self.dbname, charset='utf8', init_command='set names utf8')
		except mysql.Error as error:
			raise TwitterDBException(error=error)


	def add_places(self, places):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for place in places:
					cursor.execute(' '.join( \
					["insert ignore into geomap_place", \
					"(name, woeid, parent_id, placetype_id) values", \
					"('%s', '%s', '%s', (%s));" % (place.get('name'), \
					place.get('woeid'), place.get('parent_id'), \
					"select id from geomap_placetype where name = '%s'" \
					% place.get('placetype'))]))
				cursor.fetchall()
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)

	def get_places(self):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor(mysql.cursors.DictCursor)) as cursor:
				cursor.execute("select name, woeid, datetime from geomap_place "
						"where placetype_id = (select id from geomap_placetype "
						"where name = 'town'); ")
				cities = cursor.fetchall()
				cursor.execute("select name, woeid, datetime from geomap_place "
						"where placetype_id = (select id from geomap_placetype "
						"where name = 'country'); ")
				countries = cursor.fetchall()
				self.db.commit
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)
		return countries, cities


	# TODO update functions according to new model in databse and check all functions
	def add_trends(self, trends, datetime, woeid):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for trend in trends:
					cursor.execute(' '.join([ \
					"insert into geomap_trend", \
					"(name, volume, datetime, woeid) values", \
					"('%s', '%s', '%s', '%s');" % (trend['name'], trend['tweet_volume'], \
					datetime, woeid) \
					]))
				cursor.fetchall()
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)






