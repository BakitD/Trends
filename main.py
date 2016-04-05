import logging


from twitter_app import TwitterApp
from settings import TOKENS



def main():
	app = TwitterApp(TOKENS.consumer_key, TOKENS.consumer_secret)
	app.run()















if __name__ == '__main__':
	main()
