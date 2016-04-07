import MySQLdb as mysql

class TwitterDBException(Exception):
	def __init__(self, error='', *args, **kwargs):
		self.error = error
		super(Exception, self).__init__(error,  *args, **kwargs)


class TwitterDB:
	def __init__(self):
		self.db = None
		self.user = None
		self.host = None
		self.password = None
		self.dbname = None


	def connect(self, user, password, db, host='localhost'):
		try:
			self.db = mysql.connect( \
				host=host, user=user, \
				passwd=password, db=db)
			self.user = user
			self.password = password
			self.dbname = db
			self.host = host
		except mysql.Error as error:
			raise TwitterDBException(error=error)

	def reconnect(self):
		try:
			self.db = mysql.connect( \
				host=self.host, user=self.user, \
				passwd=self.password, db=self.db)
		except mysql.Error as error:
			raise TwitterDBException(':'.join(\
					['DB reconnect failure', str(error)]))


	def add_country(self, countries):
		try:
			with self.db:
				cursor = self.db.cursor()
				for country in countries:
					cursor.execute(' '.join( \
					["insert ignore into geomap.geomap_country", \
					"(name, woeid) values ('%s', '%s');" \
					% (country.get('name').encode('utf8'), \
					country.get('woeid'))]))
				self.db.commit()
		except mysql.Error as error:
			raise TwitterDBException(error=error)


	def add_city(self, cities):
		try:
			with self.db:
				cursor = self.db.cursor()
				for city in cities:
					cursor.execute(' '.join( \
					["insert ignore into geomap_city", \
					"(name, woeid, country_id) values ", \
					"('%s', '%s'," % (city.get('name').encode('utf8'), city.get('woeid')),
					"(select id from geomap_country where name = '%s'));" \
					% (city.get('country').encode('utf8'))]))
				self.db.commit()
		except mysql.Error as error:
			raise TwitterDBException(error=error)

				






'''
def test():
	db = TwitterDB()
	db.connect(user='root', password='passsword', db='geomap')

try:
	test()
except TwitterDBException as exc:
	print '>>>>>>>>>>>>', exc.message

'''
