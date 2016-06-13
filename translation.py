import pickle
import MySQLdb as mysql
from settings import DB
from contextlib import closing

import textblob
from textblob import TextBlob

TRANSLATE_TO = 'ru'

db = mysql.connect(host=DB.host, user=DB.user, \
			passwd=DB.password, \
			db=DB.db, charset='utf8', init_command='set names utf8')

def save_translations(places):
	with closing(db.cursor()) as cursor:
		for name, another_name in places.iteritems():
			print name, another_name
			insert = u"update place set another_name = %s where name = %s;"
			cursor.execute(insert, (another_name, name))
		db.commit()

def get_places():
	places = None
	with closing(db.cursor()) as cursor:
		cursor.execute("select name from place;")
		places = list(cursor)
		db.commit
	return [p[0] for p in places]



def translate(places):
	result = {}
	for place in places:
		word = TextBlob(place)
		try:
			tword = word.translate(to=TRANSLATE_TO).words[0]
			result[place] = unicode(tword).encode('utf-8')
		except textblob.exceptions.NotTranslated:
			result[place] = place
	return result


def main():
	places = get_places()
	result = translate(places)
	save_translations(result)


if __name__ == '__main__':
	main()
