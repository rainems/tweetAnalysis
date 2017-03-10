import cPickle as pickle
import requests

SEARCH_QUERY = 'mcdonalds'

r = requests.get(
    'https://api.twitter.com/1.1/search/tweets.json',
    headers={'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAAPmnzQAAAAAAxzT5faTu7o8yoaGOZUnZNg4aI%2Fw%3D63F29Y6ioiJ9lYqucBzOC4Y707S0YPKbgioLqGF9bzxmFsdTUr'},
    params={
        'q': SEARCH_QUERY,
    },
)

# response is a dictionary that the twitter api returned
# see https://dev.twitter.com/rest/reference/get/search/tweets for schema
response = r.json()

# save this response to a file for safekeeping
# with open('search_response.pickle', 'wb') as f:
#    pickle.dump(r.json(), f, protocol=2)

# to retrieve the example:
# with open('search_response.pickle', 'rb') as f:
#     response = pickle.load(f)
