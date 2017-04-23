#!/usr/bin/env python
import requests
import re
import nltk
import twitter
import csv
import math
import sklearn as skl
import numpy as np
import cPickle
import os

kTestTrainingSplitRatio = 0.2

class TweetAnalysis:
  def __init__(self):
    self.twitter = twitter.Twitter(auth=twitter.OAuth('2223635090-IaNrBG3WiiPnWTVtxupFCgB5TXAtlzKeQYRdrKu',
                                 'PDfV4DDZjB4T2EbnVAzsZCdDUMNJYDPLYlYErfuhcTNPE',
                                 'nrZxSV89t9pvZsbWHjXs7Y8vZ',
                                 'FQA4pFzrPWgVCbsUu5nXi5eWbH2T1gD7bkDAogtRmyTjzUjxNO'))
    # container for raw training data, loaded from csv
    self.training_data = []
    self.test_data = []

    # api response object (dict extracted from api json response)
    self.api_response_raw = None
    # main container holding our tweet data in a nicer format with only the fields we care about
    self.tweets = []
    # grab list of stopwords from nltk, returns list of strings
    self.stopwords = nltk.corpus.stopwords.words('english')
    # add some extra stop words specific to our use case
    self.addExtraStopWords()
    
  def addExtraStopWords(self):
    extra_stopwords = ["and"]
    for sw in extra_stopwords:
      self.stopwords.append(sw.lower())

  # Set raw data from outside class
  def addRaw(self, api_response):
    self.api_response_raw = api_response
    self.extractRaw()

  # Convert raw response into a data structure that we can use more easily
  # Here we choose a list of dictionaries where each dictionary contains relevant info about each tweet
  def extractRaw(self):
    # iterate over each raw tweet in the api response and save just the data we want
    cnt = 0
    for r in self.api_response_raw['statuses']:
      self.tweets.append(
        {
          "user":r['user']['screen_name'].encode("utf-8"),
          "text":r['text'].encode("utf-8"),
          "name":r['user']['name'],
          "retweets":r['retweet_count'],
          "favorites":r['favorite_count'],
          "created_at":r['created_at'],
          "followers_count":r['user']['followers_count'],
          "sentiment":None
        })
      cnt = cnt + 1
    print("Extracted {} tweets from raw response".format(cnt))

  def fetchRaw(self, query, count):
    print("Fetching data from twitter api with query: {} | count: {}".format(query, count))
    # response is a dictionary that the twitter api returned
    # tweet information is stored within list under the key "statuses" inside the outer most dict
    # see https://dev.twitter.com/rest/reference/get/search/tweets for schema
    self.api_response_raw = self.twitter.search.tweets(q=query, count=count)
    print("Fetched {} raw tweets from api".format(len(self.api_response_raw.get('statuses'))))
    self.extractRaw()

  def clean(self, list_of_tweets):
    if len(list_of_tweets) == 0:
      print("Cannot clean data, tweets list is empty")
      return
    # let's first drop all RTs since we just care about user mentions
    original_cnt = len(list_of_tweets)
    list_of_tweets = [w for w in list_of_tweets if "RT @" not in w['text']]
    print("Removed {} retweets from our tweets list".format(original_cnt - len(list_of_tweets)))

    progress_cnt = 0
    for tweet_dict in list_of_tweets:
      # print("Before clean:\n{}".format(tweet_dict['text']))
      # remove urls from tweet string
      tweet_dict['text'] = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', tweet_dict['text'])
      # strip punctuation
      tweet_dict['text'] = re.sub(r'[^a-zA-Z]', ' ', tweet_dict['text'])
      # strip emojiis
      emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
        "+", flags=re.UNICODE)
      tweet_dict['text'] = emoji_pattern.sub(r'', tweet_dict['text'])
      # make all words lowercase
      tweet_dict['text'] = tweet_dict['text'].lower()
      tweet_text_split = tweet_dict['text'].split()
      # remove stop words from nltk corpus
      tweet_text_split = [w for w in tweet_text_split if not w in self.stopwords]
      # remove user if in the tweet string
      tweet_dict['text'] = " ".join(tweet_text_split)
      # print(tweet_text_split)
      # print("After clean:\n{}".format(tweet_dict['text']))
      if progress_cnt % 10000 == 0: 
        print("Cleaning tweet {} of {} | {:0.1f} %".format(progress_cnt, len(list_of_tweets), (float(progress_cnt)/float(len(list_of_tweets))*100)))
      progress_cnt = progress_cnt + 1
    print("Cleaned {} tweets".format(len(list_of_tweets)))
    return list_of_tweets

  def loadTrainingData(self, filepath):
    pickle_filepath = filepath + ".pickle"
    if not os.path.isfile(pickle_filepath):
      print("Loading training data from {}, please wait...".format(filepath))
      with open(filepath) as f:
        for row in csv.DictReader(f, skipinitialspace=True):
          self.training_data.append(row)
      print("Loaded training data: {} tweets".format(len(self.training_data)))
      # clean our training data
      print("Cleaning training data set. This could take a while...")
      self.training_data = self.clean(self.training_data)
      # dump the training data to a pickle file so we dont have to do this every time
      with open(pickle_filepath, "wb") as f:
        cPickle.dump(self.training_data, f, cPickle.HIGHEST_PROTOCOL)
      print("Wrote training data to pickle: {}".format(pickle_filepath))
    else:
      print("Found pickle file with training data.")
      print("Loading training set from: {}".format(pickle_filepath))
      self.training_data = cPickle.load(open(pickle_filepath, "rb"))

    # split the training data into test and training sets
    size_of_dataset = len(self.training_data)
    index_for_split = int(size_of_dataset * kTestTrainingSplitRatio)
    print("Splitting dataset into test/training by ratio {} at index {} of {}".format(kTestTrainingSplitRatio, index_for_split, len(self.training_data)))
    self.test_data = self.training_data[:index_for_split]
    self.training_data = self.training_data[index_for_split:]

  def buildTrainingModel(self):
    self.forest_classifier = skl.ensemble.RandomForestClassifier(n_estimators=50)
    self.forest_classifier = self.forest_classifier.fit()

if __name__ == "__main__":
  ta = TweetAnalysis()
  ta.loadTrainingData("sentiment_training_set.csv")
  # ta.fetchRaw("@united", 5)
  # ta.setRaw(api_response_from_app)
  # ta.tweets = ta.clean()
