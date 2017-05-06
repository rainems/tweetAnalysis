#!venv/bin/python
import os
import time
import json
import numpy as np
import twitter
from flask import Flask, request, render_template, redirect, abort, flash, jsonify
from random import randint
import collections
from sklearn.externals import joblib
from sklearn.linear_model import SGDRegressor

sentiment_clf = joblib.load('checkpoints/reg.pkl')
vectorizer = joblib.load('checkpoints/vectorizer.pkl')

app = Flask(__name__)   # create our flask app

# configure Twitter API
api = twitter.Twitter(auth=twitter.OAuth(
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
            'words': '',
        }
    else:  # POST request
        keywords = request.form.get('keywords', '').strip()
        exclude = request.form.get('exclude', '').strip()
        from_user = request.form.get('from_user', '').strip()
        to_user = request.form.get('to_user', '').strip()

        query = ' '.join((
            keywords,
            ('-' + ' -'.join(exclude.split())) if exclude else '',  # excludes
            ('from:' + from_user) if from_user else '',  # from user
            ('to:' + to_user) if to_user else '',  # to user
        ))
        query += ' -filter:retweets'
        print(query)
        results = api.search.tweets(q=query, count=100).get('statuses')

        if len(results) == 0:
            templateData = {
                'title': 'Twitter Analysis',
                'words': '',
            }
            return render_template('index.html', **templateData)

        print('results:', len(results))
        tweets = classify_tweet_sentiments(results)
        tweet_buckets = get_sentiment_buckets(tweets)

        templateData = {
            'title': 'Search results',
            'tweet_buckets': tweet_buckets,
            'keywords': keywords,
            'exclude': exclude,
            'from_user': from_user,
            'to_user': to_user,
            'words': get_tweets_words(tweet_buckets['pos']),
        }

    return render_template('index.html', **templateData)


def classify_tweet_sentiments(tweets, clf=sentiment_clf):
    tweet_strs = np.array([t['text'] for t in tweets])
    vectorized = vectorizer.transform(tweet_strs)
    sentiments = clf.predict(vectorized).round(2).clip(0, 1)
    for i, tweet in enumerate(tweets):
        tweet.update({'sentiment': sentiments[i]})
    return tweets


def get_tweets_words(tweets):
    """
    wordcounts = {}
    words = []
    for tweet in tweets:
        words.extend(tweet['text'].strip().split())
    for word in words:
        wordcounts[word] = wordcounts.get(word, 0) + 1
    ret = [{'text': k, 'size': wordcounts[k]} for k in wordcounts]
    """
    
    return [' '.join(t['text'] for t in tweets)]


def get_sentiment_buckets(tweets, thresholds=[0.4, 0.6]):
    buckets = {
        'neg': [],
        'neu': [],
        'pos': [],
    }
    for tweet in tweets:
        if tweet['sentiment'] > thresholds[1]:  # positive tweet
            buckets['pos'].append(tweet)
        elif tweet['sentiment'] >= thresholds[0]:
            buckets['neu'].append(tweet)
        else:
            buckets['neg'].append(tweet)
    buckets['neu'][:100].sort(key=lambda t: t['sentiment'], reverse=True)
    buckets['pos'].sort(key=lambda t: t['sentiment'], reverse=True)
    buckets['neg'].sort(key=lambda t: t['sentiment'])
    return buckets


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    pyDate = time.strptime(date,'%a %b %d %H:%M:%S +0000 %Y') # convert twitter date string into python date/time
    return time.strftime('%Y-%m-%d %H:%M:%S', pyDate) # return the formatted date.
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
