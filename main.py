import logging

from settings import TOKENS, DB
from twitter_app import TwitterApp
from twitter_db import TwitterDB


def main():
	db = TwitterDB(user=DB.user, password=DB.password, dbname=DB.db)
	db.connect()
	app = TwitterApp(TOKENS.consumer_key, TOKENS.consumer_secret, db)
	app.run()



if __name__ == '__main__':
	main()
