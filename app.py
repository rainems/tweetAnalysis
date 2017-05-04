#!venv/bin/python
import os
import time
import json
import numpy as np
from twitter import *
from flask import Flask, request, render_template, redirect, abort, flash, jsonify
from geopy.geocoders import Nominatim
from random import randint
import collections
from sklearn.externals import joblib
from sklearn.linear_model import SGDRegressor

sentiment_clf = joblib.load('checkpoints/reg.pkl')
vectorizer = joblib.load('checkpoints/vectorizer.pkl')

geolocator = Nominatim()

app = Flask(__name__)   # create our flask app

# configure Twitter API
twitter = Twitter(auth=OAuth(
    '2223635090-IaNrBG3WiiPnWTVtxupFCgB5TXAtlzKeQYRdrKu',
    'PDfV4DDZjB4T2EbnVAzsZCdDUMNJYDPLYlYErfuhcTNPE',
    'nrZxSV89t9pvZsbWHjXs7Y8vZ',
    'FQA4pFzrPWgVCbsUu5nXi5eWbH2T1gD7bkDAogtRmyTjzUjxNO',
))

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        templateData = {
            'title': 'Twitter Analysis',
        }
    else:  # POST request
        keywords = request.form.get('keywords', '')
        location = request.form.get('location', '')
        if location:
            geocode = get_geocode_from_str(location)
        else:
            geocode = '' 

        results = twitter.search.tweets(q=keywords, geocode=geocode, count=100).get('statuses')

        classify_tweet_sentiments(results)

        #Temporary lists to be replaced with sentiment analysis
        positive = results[0:20]
        neutral = results[20:40]
        negative = results[40:60]
        
        templateData = {
            'title': 'Search results',
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'keywords': keywords,
            'location': location,
        }

    return render_template('index.html', **templateData)


def classify_tweet_sentiments(tweets, clf=sentiment_clf):
    tweet_strs = np.array([t['text'] for t in tweets])
    vectorized = vectorizer.transform(tweet_strs)
    sentiments = clf.predict(vectorized).round(2)
    for i, tweet in enumerate(tweets):
        tweet.update({'sentiment': sentiments[i]})
    return tweets


def get_geocode_from_str(geo_query):
    #Use google maps to get location from name
    geo_obj = geolocator.geocode(geo_query)
    #Search String for twitter Api
    geocode = str(geo_obj.latitude) + ',' + str(geo_obj.longitude) + ',50mi'
    #Get google maps correct term for place
    geo_query = str(geo_query).split(',')[0]
    return geo_query


def interpolate_missing_locations(tweets):
    c = collections.Counter()
    for tweet in tweets:
        if tweet['place']:
            c.update([tweet['place']['full_name']])
    place = c.most_common(1)
    place = place[0][0]
    return place


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    pyDate = time.strptime(date,'%a %b %d %H:%M:%S +0000 %Y') # convert twitter date string into python date/time
    return time.strftime('%Y-%m-%d %H:%M:%S', pyDate) # return the formatted date.
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
