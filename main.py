import logging

from settings import TOKENS, DB
from twitter_app import TwitterApp
from twitter_db import TwitterDB


def main():
	db = TwitterDB()
	db.connect(user=DB.user, password=DB.password, db=DB.db)
	app = TwitterApp(TOKENS.consumer_key, TOKENS.consumer_secret, db)
	app.run()





if __name__ == '__main__':
	main()
