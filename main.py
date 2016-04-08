import logging

from settings import TOKENS, DB, LOG
from settings import IS_DEBUG
from twitter_app import TwitterApp
from twitter_db import TwitterDB


def main():
	if IS_DEBUG:
		logging.basicConfig(level=logging.DEBUG, format=LOG.log_format, \
					datefmt=LOG.date_format)
	else:
		logging.basicConfig(filename=LOG.filename, level=logging.DEBUG, \
					format=LOG.log_format, datefmt=LOG.date_format)
	db = TwitterDB(user=DB.user, password=DB.password, dbname=DB.db)
	db.connect()
	app = TwitterApp(TOKENS.consumer_key, TOKENS.consumer_secret, db)
	app.run()



if __name__ == '__main__':
	main()
