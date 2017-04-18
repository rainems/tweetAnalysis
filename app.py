#!venv/bin/python
import os
import time
from twitter import *
from flask import Flask, request, render_template, redirect, abort, flash, jsonify

app = Flask(__name__)   # create our flask app

# configure Twitter API
twitter = Twitter(
            auth=OAuth('2223635090-IaNrBG3WiiPnWTVtxupFCgB5TXAtlzKeQYRdrKu',
                'PDfV4DDZjB4T2EbnVAzsZCdDUMNJYDPLYlYErfuhcTNPE',
                       'nrZxSV89t9pvZsbWHjXs7Y8vZ',
                       'FQA4pFzrPWgVCbsUu5nXi5eWbH2T1gD7bkDAogtRmyTjzUjxNO')           

           )

@app.route('/')
def main():
    query = request.args.get('q', False)
    if query:
        # search with query term and return 10
        results = twitter.search.tweets(q=query, count=50)
        
        templateData = {
            'title': 'Search results',
            'header' : 'Query: ' + query,
            'tweets' : results.get('statuses'),
        }

    else:
        # fetch 3 tweets from my account
        myTweets = twitter.statuses.user_timeline(count=10)

        templateData = {
            'title': 'My tweets',
            'header' : 'My last three tweets',
            'tweets' : myTweets,
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


