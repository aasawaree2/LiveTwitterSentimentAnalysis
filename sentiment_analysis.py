
# coding: utf-8

# In[1]:


# Importing Libraries
import json  #Read json file for authentication
import pandas as pd
import matplotlib.pyplot as plt #plot map using plt
from mpl_toolkits.basemap import Basemap #plt map using basemap
import twitter #Twitter API
from twitter import * #Twitter API
import csv #Read and write CSV file
import tweepy #Livestreaming tweepy library
import re
import datetime as dt #Date and Time
import time
import os
import sys 
from textblob import TextBlob #Sentiment Anaylsis
from ipywidgets import IntProgress, HTML, VBox #Progress Bar
from IPython.display import display # Progress Bar display
from time import sleep #Sleep timet
from bokeh.layouts import row, widgetbox , column
from bokeh.models.widgets import TextInput, Button
from bokeh.io import curdoc
from bokeh.models import Select
from bokeh.events import ButtonClick
from bokeh.models import Button

from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, GMapOptions
from bokeh.plotting import gmap

import numpy as np

from bokeh.palettes import Spectral5
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Div
from bokeh.plotting import figure

# In[2]:


# Loading my authentication tokens
with open('auth_dict3.json','r') as f:
    twtr_auth = json.load(f)

#Loading Authentication Keys
CONSUMER_KEY = twtr_auth['consumer_key']
CONSUMER_SECRET = twtr_auth['consumer_secret']
OAUTH_TOKEN = twtr_auth['token']
OAUTH_TOKEN_SECRET = twtr_auth['token_secret']
    
# Then, we store the OAuth object in "auth"
auth = OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                           CONSUMER_KEY, CONSUMER_SECRET)
# Notice that there are four tokens - you need to create these in the
# Twitter Apps dashboard after you have created your own "app".

# We now create the twitter search object.
twitter = Twitter(auth=auth)


# In[3]:


# Create CSV File and add a header 
with open('jinx1.csv', 'wb') as csvfile:
    fieldnames = ["Text", "longitude" , "latitude", "sentiment"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()


# In[4]:


#check_sentiment function is use to check the sentiment of the tweets
def check_sentiment(text):
    #Sentiment Analysis on every tweets
    analysis = TextBlob(text)

    #Categorizing tweet on the basis of sentiment
    sentiment = ''
    if analysis.sentiment.polarity > 0:
        sentiment = 'positive'
    elif analysis.sentiment.polarity == 0:
        sentiment = 'neutral'
    else:
        sentiment = 'negative'
    
    return sentiment


# In[5]:


def add_data(Text,longitude,latitude,sentiment):
    with open('jinx1.csv', 'ab') as csvfile:
        fieldnames = ["Text", "longitude" , "latitude", "sentiment"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'Text': Text, 'longitude': longitude, 'latitude': latitude, 'sentiment':sentiment })


# In[6]:


def tweet_search(api, query, limit, max_id, since_id, layout):

    total_tweets = []
    while len(total_tweets) < limit:
        remaining_tweets = limit - len(total_tweets)
        try:
            #Calling tweets equal to limit
            new_tweets = api.search(q=query, count=remaining_tweets,
                                    since_id=str(since_id),
                                    max_id=str(max_id-1))

            #print('found ' + str(len(new_tweets)) +' tweets')

            if not new_tweets:
                print('no tweets found')
                break
            
            total_tweets.extend(new_tweets)
            max_id = new_tweets[-1].id
            
            for tweet in new_tweets:
                if tweet._json['coordinates'] is not None:
                    text1 = tweet._json['text']
                    #Filter tweets
                    text = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text1).split())
                    
                    text = text.encode('ascii', 'replace') 
                    #Sentiment Analysis
                    sentiment = check_sentiment(text)
                
                    lang = tweet._json['coordinates']['coordinates'][0]
                    lat = tweet._json['coordinates']['coordinates'][1]
                    
                    #Adding tweets and coordinates to CSV file
                    add_data(text,lang,lat,sentiment)
                                   
        except tweepy.TweepError:
            layout.children[0] = display_message("Wait for 15 minutes" + '(until:', dt.datetime.now()+dt.timedelta(minutes=15), ')')

            time.sleep(15*60)
            break 
    return total_tweets, max_id


# In[7]:


def get_tweet_id(api, date='', days_ago=9, query='a'):
    ''' Function that gets the ID of a tweet. This ID can then be
        used as a 'starting point' from which to search. The query is
        required and has been set to a commonly used word by default.
        The variable 'days_ago' has been initialized to the maximum
        amount we are able to search back in time (9).'''

    if date:
        # return an ID from the start of the given day
        td = date + dt.timedelta(days=1)
        tweet_date = '{0}-{1:0>2}-{2:0>2}'.format(td.year, td.month, td.day)
        tweet = api.search(q=query, count=1, until=tweet_date)
    else:
        # return an ID from __ days ago
        td = dt.datetime.now() - dt.timedelta(days=days_ago)
        tweet_date = '{0}-{1:0>2}-{2:0>2}'.format(td.year, td.month, td.day)
        # get list of up to 10 tweets
        tweet = api.search(q=query, count=10, until=tweet_date)
        
        # return the id of the first tweet in the list
        return tweet[0].id


# In[8]:


class TwitterStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        self.get_tweet(status)

    def on_error(self, status_code):
        if status_code == 420:
            print("The request is understood, but it has been refused or access is not allowed. Limit is maybe reached")
            return False
    
    @staticmethod
    def get_tweet(tweet):
        if tweet.coordinates is not None:
            # Refining the tweets
            text = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet.text).split())
            text = text.encode('ascii', 'replace') 
            
            sentiment = check_sentiment(text)
            
            # Extrating Coordinates
            longitude = tweet.coordinates['coordinates'][0]
            latitude = tweet.coordinates['coordinates'][1]
            
            #inserting into CSV File
            add_data(text,longitude,latitude,sentiment)

# In[12]:


def main(hashtag , days , layout, button , sentiment , continent, button1):
    
    # Authentication
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.secure = True
    auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=10, retry_delay=5,
                     retry_errors=5)
    
    time_limit = 1.5
    limit = 100
    max_days_old = days
    if(max_days_old == 0):
        max_days_old = 1
    min_days_old = 0
    
    if max_days_old - min_days_old == 1:
        d = dt.datetime.now() - dt.timedelta(days=min_days_old)            
        day = '{0}-{1:0>2}-{2:0>2}'.format(d.year, d.month, d.day)
        day = "for " + day
        
    else:
        d1 = dt.datetime.now() - dt.timedelta(days=max_days_old-1)
        d2 = dt.datetime.now() - dt.timedelta(days=min_days_old)
        day = '{0}-{1:0>2}-{2:0>2}_to_{3}-{4:0>2}-{5:0>2}'.format(
              d1.year, d1.month, d1.day, d2.year, d2.month, d2.day)
        day = "from " +day
        
    layout.children[0] = display_message("Fetching data "+ day +" Wait for some time" )    
    if min_days_old == 0:
        max_id = -1
    else:
        max_id = get_tweet_id(api, days_ago=(min_days_old-1))

    since_id = get_tweet_id(api, days_ago=(max_days_old-1))
    
    counter = 0

    while counter <= 11000:
        tweets, max_id = tweet_search(api, hashtag, limit,
                                  max_id=max_id, since_id=since_id, layout = layout)
        counter = counter + 100
        layout.children[0] = display_message("Total tweets fetched "+ str(counter) +" from 11000" )
    
    button.disabled = False
    button.button_type = "success"
    sentiment.disabled = False
    continent.disabled = False
    continent.value = "Asia"
    button1.disabled = False
    button1.button_type = "success"
    
    streamListener = TwitterStreamListener()
    #create_CVS_File()
    myStream = tweepy.Stream(auth=api.auth, listener=streamListener)

    #myStream.filter(locations=[-180, -90, 180, 90], async=True)

    myStream.filter(track=[hashtag], async=True)
    #csvfile.close()
    layout.children[0] = display_message("Fetching real time/live tweets containing word "+ hashtag+ "\n"+" Click On Refresh Button or change the continents to view results")

# In[13]:
def display_message(message):
    message_box = Div(text=message, height=50)
    return message_box

#Run the main function to start the program
def start_program():
    # Set up widgets
    text = TextInput(title="HashTag", value='HashTag')
   
    columns = ['Today','From yesterday','Two days ago','Three days ago','Four days ago','Five days ago','Six days ago']
    days = Select(title='Days', value='Today' , options=columns)

    button = Button(label="Fetch Data", button_type="success")
    button1 = Button(label="Refresh", button_type="danger" , disabled = True)
    
    #def display_message(message):
    message_box = Div(text="Welcome")

    def callback(event):
        if(text.value == ""):
            layout1.children[0] = display_message("HashTag should not be Empty")
            return
        button.disabled = True
        button.button_type = "danger"
        sentiment.disabled = True
        continent.disabled = True
        button1.disabled = True
        button1.button_type = "danger"
        
        old = 0
        if(days.value == "Today"):
            old = 0
        elif(days.value == "From yesterday"):
            old = 1
        elif(days.value == "Two days ago"):
            old = 2
        elif(days.value == "Three days ago"):
            old = 3
        elif(days.value == "Four days ago"):
            old = 4
        elif(days.value == "Five days ago"):
            old = 5 
        else:
            old = 6                 
        main(hashtag = text.value, days = old, layout = layout1 , button = button , sentiment = sentiment , continent = continent , button1 = button1)
       

    button.on_event(ButtonClick, callback)
    
    def create_figure(event):
        conti = continent.value
        senti = sentiment.value

        if(conti == "North America"):
            map_options = GMapOptions(lat=33.465777, lng=-88.369025, map_type="roadmap", zoom=3)
        elif(conti == "South America"):
            map_options = GMapOptions(lat=-8.783195, lng=-55.491477, map_type="roadmap", zoom=3)
        elif(conti == "Africa"):
            map_options = GMapOptions(lat=-8.783195, lng=34.508523, map_type="roadmap", zoom=3)
        elif(conti == "Asia"):
            map_options = GMapOptions(lat=34.047863, lng=100.619655, map_type="roadmap", zoom=3)
        elif(conti == "Europe"):
            map_options = GMapOptions(lat=54.525961, lng=15.255119, map_type="roadmap", zoom=3)
        elif(conti == "Antartica"):
            map_options = GMapOptions(lat=-82.862752, lng=135.000000, map_type="roadmap", zoom=3)
        else:
            map_options = GMapOptions(lat=-25.274398, lng=133.775136, map_type="roadmap", zoom=3)

        p = gmap("AIzaSyCJMprrXTtmUqciVaVgskmHxskLkVjrE6A", map_options, title="World Map" , width = 950)
        p.circle(None,None, size=5, fill_color="green", fill_alpha=0.7, legend = "Positive")
        p.circle(None,None, size=5, fill_color="yellow", fill_alpha=0.7, legend = "Neutral")
        p.circle(None,None, size=5, fill_color="red", fill_alpha=0.7, legend = "Negative")
        def load(data):
            lat = []
            lon = []

            with open('jinx1.csv') as csvfile:
                reader = csv.DictReader(csvfile)    
                for row in reader:
                    x = float(row["longitude"])
                    y = float(row["latitude"])
                    z = row["sentiment"]
                    if(z == data):
                        lat.append(y)
                        lon.append(x)
            data1 = dict(lat=lat,lon=lon)
            return data1
        
        if(senti == "All"):
            source = ColumnDataSource(data=load(data="positive"))
            p.circle(x="lon", y="lat", size=8, fill_color="green", fill_alpha=1.0, source=source)
            source = ColumnDataSource(data=load(data="negative"))
            p.circle(x="lon", y="lat", size=8, fill_color="red", fill_alpha=1.0, source=source)
            source = ColumnDataSource(data=load(data="neutral"))
            p.circle(x="lon", y="lat", size=8, fill_color="yellow", fill_alpha=1.0, source=source)
        elif(senti == "Positive"):
            source = ColumnDataSource(data=load(data="positive"))
            p.circle(x="lon", y="lat", size=8, fill_color="green", fill_alpha=1.0, source=source)
        elif(senti == "Negative"):
            source = ColumnDataSource(data=load(data="negative"))
            p.circle(x="lon", y="lat", size=8, fill_color="red", fill_alpha=1.0, source=source)
        else:
            source = ColumnDataSource(data=load(data="neutral"))
            p.circle(x="lon", y="lat", size=8, fill_color="yellow", fill_alpha=1.0, source=source)            


        return p
    
    def update(attr, old, new):
        layout.children[1] = create_figure(event = None)
    
    def update1():
        layout.children[1] = create_figure(event = None)
        
    button1.on_click(update1)
    
    #Set all Parameters
    columns = ["All","Positive","Neutral","Negative"]
    sentiment = Select(title='Sentiment', value='All', options=columns , disabled = True)
    sentiment.on_change('value', update)

    continents = ["North America","South America", "Africa" , "Asia" , "Antartica" , "Europe" , "Australia"]
    continent = Select(title='Continents', value='North America', options=continents, disabled = True)
    continent.on_change('value', update)

    # Set up layouts and add to document
    controls = widgetbox([text, days, button ,sentiment , continent, button1])
    layout1 = column(display_message("Welcome"),controls)
    layout = row(layout1 , create_figure(event = None))
    
    curdoc().add_root(layout)
    curdoc().title = "World Map"

# In[14]:

start_program()