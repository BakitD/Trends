import logging

from settings import DB, LOG, MEM
from settings import IS_DEBUG
from settings import TWITTER_CONFIG_FILE

from twitter_app import TwitterApp
from twitter_db import TwitterDB
from twitter_mem import TwitterMem


def main():
	if IS_DEBUG:
		logging.basicConfig(level=logging.DEBUG, format=LOG.log_format, \
					datefmt=LOG.date_format)
	else:
		logging.basicConfig(filename=LOG.filename, level=logging.DEBUG, \
					format=LOG.log_format, datefmt=LOG.date_format)
	db = TwitterDB(user=DB.user, password=DB.password, dbname=DB.db)
	memdb = TwitterMem(prefix=MEM.prefix, host=MEM.host, port=MEM.port)
	db.connect()
	app = TwitterApp(TWITTER_CONFIG_FILE, db, memdb)
	app.run()



if __name__ == '__main__':
	main()
