import MySQLdb as mysql
import base64
from contextlib import closing

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


	def add_country(self, countries):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for country in countries:
					cursor.execute(' '.join( \
					["insert ignore into geomap.geomap_country", \
					"(name, woeid) values ('%s', '%s');" \
					% (country.get('name'), \
					country.get('woeid'))]))
				cursor.fetchall()
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)


	def add_city(self, cities):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for city in cities:
					cursor.execute(' '.join( \
					["insert ignore into geomap_city", \
					"(name, woeid, country_id) values ", \
					"('%s', '%s'," % (city.get('name'), city.get('woeid')),
					"(select id from geomap_country where name = '%s'));" \
					% (city.get('country'))]))
				cursor.fetchall()
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)

				

