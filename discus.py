# If you're erroring out on this, read my_token.py
from data.my_token import my_token, my_collection, my_wantlist

# imports for data science and API requests
import numpy as np
import pandas as pd
import time
import requests

# grab collections as indicated by my_token.py 
mine = pd.read_csv(my_collection)
want = pd.read_csv(my_wantlist, index_col=False)

# discogs API URL
d_api = 'https://api.discogs.com/'

####### TODO todo:
# 
# wantlist:
#   my_rating (then I can use the stars in discogs to rank 1-5 how badly I want each record)
#       ->> TODO: bring this in, my_rating
#
# marketplace:
#   check sellers' inventory for other items from wantlist
# RSS SEARCH MARKETPLACE:
# https://www.discogs.com/sell/release/4922985?output=rss
#
# ML:
#   compare to historical prices, decide whether it's a good price or not. 
#
#######

class fetcher:
    '''
    Class to fetch the info from df by release_id column, 
    passing discogs_field into the method call for fetch_json()
    '''

    def __init__(self, df):
        '''
        Take the DataFrame passed on instantiation and store in self.df
        self.fetched_list is used to store values before adding to DataFrame
        '''
        self.fetched_list = []
        self.ids = []
        self.df = df

    def fetch_json(self, i, discogs_field):
        '''
        Call requests.get, inheriting the counter i from self.find(), being passed discogs_field
        to determine data requested. Attach JSON data to self.fetched_list.
        
        TODO: turn fetched_list into fetched_dict and make it release_id : JSON object
        Discogs API request for specified record and field.
        '''
        
        # make the request
        self.json_raw = requests.get(f"{d_api}/{discogs_field}/{self.df.release_id[i]}",
                                params={'token': my_token})

        # Append to attribute fetched_list if it's not a message telling me I've sent
        # too many requests. Or wait 10s and try again.
        if "message" in self.json_raw.json().keys():
            for second in range(1,30):
                time.sleep(1)
                print(f'sleeping bc discogs asked us to: {second}') 
            self.fetch_json(i, discogs_field)
        else:
            self.fetched_list.append(self.json_raw.json())
            self.ids.append(self.df.release_id[i])
        
        return self

    def find(self, discogs_field):
        '''
        Implements sleeper function required to stay beneath Discogs' 60 requests/minute.
        Calls fetch_json, which stores the JSON elements in fetched_list - which still needs to
        be added to Pandas DataFrames with stitch_price(), or other methods designed later to deal
        with other use cases.
        '''
        # iterate through passed DataFrame's release_id column.
        for i in range(len(self.df['release_id'])):
            # TODO: VERIFY THAT THIS LOOP IS NOT CAUSING AN OFF-BY-ONE UPON STITCHING
            if (i % 59 == 0 and i != 0):
                # sleep
                for second in range(1,60):
                    time.sleep(1)
                    print(f'sleeping {second}') 
            else:
                #API calls up to 59, no sleeping. print to keep track of progress.
                self.fetch_json(i, discogs_field)
                print(f'requesting: {self.df.iloc[i]["Title"]} by {self.df.iloc[i]["Artist"]}')
        return self

    def prep_data(self):
        '''
        Prepare newly fetched data for appending.
        '''

        self.fetched_data = pd.io.json.json_normalize(self.fetched_list)
        
        self.id_date = pd.DataFrame({
            'release_id': self.ids,
            'date': pd.datetime.now().strftime("%Y-%m-%d")
                })
        
        self.out_df = pd.concat([self.id_date, self.fetched_data], axis=1)

        return self

    def stitch_price(self):
        '''
        todo
        combines self.fetched_list with corresponding DataFrames 
        '''

        # old code:
        # self.ratings_list.append(json_raw.json()['rating']['average'])
        # which was then tacked onto the DataFrame from the collection/wantlist .csv
        return self

    def wait_til_tomorrow():
        """Wait to tommorow 00:00 am"""
        
        print('starting waiting 24h')
        tomorrow = datetime.datetime.replace(datetime.datetime.now() + datetime.timedelta(days=1), 
                         hour=0, minute=0, second=0)
        delta = tomorrow - datetime.datetime.now()
        time.sleep(delta.seconds)
        print('done waiting')

while True:
########## fetch from discogs
    myfetch = fetcher(mine)
    wantfetch = fetcher(want)
    wantfetch.find('/marketplace/price_suggestions/')

    # wantfetch.out_df should now contain a DataFrame marked with today's prices.
    print('prepping data')
    wantfetch.prep_data()
    print('saving csv')
    wantfetch.out_df.to_csv(f'data/pricefetch/wantlist_prices_{pd.datetime.now().strftime("%Y-%m-%d")}.csv', index=False)
    wait_til_tomorrow()
