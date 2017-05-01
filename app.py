#!venv/bin/python
import os
import time
import json
from twitter import *
from flask import Flask, request, render_template, redirect, abort, flash, jsonify
from geopy.geocoders import Nominatim
from random import randint
import collections
geolocator = Nominatim()

app = Flask(__name__)   # create our flask app

# configure Twitter API
twitter = Twitter(
            auth=OAuth('2223635090-IaNrBG3WiiPnWTVtxupFCgB5TXAtlzKeQYRdrKu',
                'PDfV4DDZjB4T2EbnVAzsZCdDUMNJYDPLYlYErfuhcTNPE',
                       'nrZxSV89t9pvZsbWHjXs7Y8vZ',
                       'FQA4pFzrPWgVCbsUu5nXi5eWbH2T1gD7bkDAogtRmyTjzUjxNO'))

@app.route('/')
def main():
    query = request.args.get('q', False)
    geo = request.args.get('g', "")
    
            
    if query:
        if geo:
            try:
                #Use google maps to get location from name
                geo_temp = geolocator.geocode(geo)

                #Search String for twitter Api
                geocode = str(geo_temp.latitude) + "," + str(geo_temp.longitude) + ",50mi"

                #Get google maps correct term for place
                geo = str(geo).split(',')[0]
                geo = geo[:len(geo)]

                #Search twitter API
                results = twitter.search.tweets(q=query, geocode=geocode, count=1000).get('statuses')
                
                #Interpolate missing places
                place = []
                c = collections.Counter()
                for each in results:
                    if each['place']:
                        c.update([each['place']['full_name']])
    
                place = c.most_common(1)
                place = place[0][0]
                
                

            except: #Catch when geocoder doesnt recognize the place
                results = twitter.search.tweets(q=query, count=60).get('statuses')
                place = geo

        else:  #When there is no location search parameter
            results = twitter.search.tweets(q=query, count=60).get('statuses')
            place = ""
        

        #Temporary lists to be replaced with sentiment analysis
        positive = results[0 : 20]
        neutral = results[20 : 40]
        negative = results[40 : 60]
        
        templateData = {
            'title': 'Search results',
            'header' : 'Query: ' + query,
            'positive' : positive,
	    'neutral' : neutral,
	    'negative' : negative,
        'positive_len' : len(positive) ,
        'neutral_len' : len(neutral) ,
        'negative_len' : len(negative) ,
        'query' : query,

        ##when geo is more than one word it doesnt show the second word
        'geocode' : geo,
        'place' : place
        }

    else:
	
        templateData = {
            'title': 'Twitter Analysis',
            'header' : 'Peep some tweets homie',
            'positive' : None,
	    'neutral' : None,
	    'negative' : None,
        'positive_len' : 0,
        'neutral_len' : 0 ,
        'negative_len' : 0 ,
        'query' : "",
        'geocode' : "",
        }

    return render_template('index.html', **templateData)


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    pyDate = time.strptime(date,'%a %b %d %H:%M:%S +0000 %Y') # convert twitter date string into python date/time
    return time.strftime('%Y-%m-%d %H:%M:%S', pyDate) # return the formatted date.
    
# --------- Server On ----------
# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)


