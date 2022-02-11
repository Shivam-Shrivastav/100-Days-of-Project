# !/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys

argfile = str(sys.argv[1])

#enter the corresponding information from your Twitter application:
CONSUMER_KEY = str(input('\nEnter api key: '))#keep the quotes, replace this with your consumer key
CONSUMER_SECRET = str(input('\nEnter api key secret: ')) #keep the quotes, replace this with your consumer secret key
ACCESS_KEY = str(input('\nEnter access token: ')) #keep the quotes, replace this with your access token
ACCESS_SECRET = str(input('\nEnter access token secret: ')) #keep the quotes, replace this with your access token secret
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

filename=open(argfile,encoding="utf8")
f=filename.readlines()
filename.close()
# print(tweepy.TweepyException)

for line in f:
    try:
        print(line)
        if line != '\n':
            api.update_status(line)
        else:
            pass
    except tweepy.TweepyException as e:
            print(e)
    time.sleep(14400)