import MySQLdb as mysql
import base64
from contextlib import closing
from datetime import datetime, timedelta

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


	def add_places(self, places, dtime):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for place in places:
					insert = "insert ignore into place " \
					"(name, woeid, parent_id, dtime, longitude, latitude, placetype_id) values " \
					"(%s, %s, %s, %s, %s, %s, (select id from placetype where name = %s));"
					cursor.execute(insert, (place.get('name'), place.get('woeid'), 
							place.get('parent_id'), dtime, place.get('longitude'), 
							place.get('latitude'), place.get('placetype')))
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)

	def get_woeids(self):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor(mysql.cursors.DictCursor)) as cursor:
				cursor.execute("select woeid from place")
				woeids = list(cursor)
				self.db.commit
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)
		return [element['woeid'] for element in woeids]



	def get_places(self, update_time=0):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor(mysql.cursors.DictCursor)) as cursor:
				cursor.execute("select name, woeid, dtime, longitude, latitude from place " \
						"where timestampdiff(HOUR, place.dtime, now()) >= %s;", (update_time,))
				places = list(cursor)
				self.db.commit
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)
		return places


	def add_trends(self, trends, woeid):
		try:
			if not self.db.open: self.connect()
			with closing(self.db.cursor()) as cursor:
				for trend in trends:
					insert = "insert ignore into trend (name) values (%s) " \
						"on duplicate key update id = LAST_INSERT_ID(id);"
					cursor.execute(insert, (trend['name'],))
					insert = "insert into geotrend (volume, trend_id, place_id) " \
						"values (%s, %s, (select id from place where woeid = %s));"
					cursor.execute(insert, (trend['tweet_volume'], cursor.lastrowid, woeid,))
				insert  = "update {} set dtime = %s where woeid = %s;".format('place')
				cursor.execute(insert, (datetime.now().strftime(DATETIME_FORMAT), woeid))
				self.db.commit()
			self.db.close()
		except mysql.Error as error:
			raise TwitterDBException(error=error)

