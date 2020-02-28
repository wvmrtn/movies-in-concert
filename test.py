#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 16:38:45 2020

@author: williammartin
"""

# import standard libraries
import logging
from logging import Handler
import os
import requests
import sys
# import third-party libraries
import pandas as pd
import slack
# import local libraries

# handle script if ran without arguments
if len(sys.argv) == 1:
    TO_FIND = 'interstellar'
    CHANNEL = '@URE5PNJTS'
    LEVEL = 'INFO'
else:
    TO_FIND = sys.argv[1]
    CHANNEL = sys.argv[2]
    LEVEL = sys.argv[3]

# =============================================================================
# Create logger
# =============================================================================
# get root logger
logger = logging.getLogger()
# flush handlers
logger.handlers = []

# create streamhandler overwriting root streamhandler format
format_message = '%(asctime)s %(filename)-14s %(levelname)-8s: %(message)s'
format_date = '%Y-%m-%d %H:%M:%S'
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(format_message, format_date))
logger.setLevel(logging.WARNING) # Warning because we don't want logs from other standard modules using the root logger
logger.addHandler(handler)

logger.setLevel(LEVEL)

# =============================================================================
# Slack handlers
# =============================================================================
class SlackHandler(Handler):
    
    def __init__(self, channel):
        
        Handler.__init__(self)
        self.bot_token = os.environ['SLACK_API_TOKEN_BOT_2']
        self.bot_client = slack.WebClient(token = self.bot_token)
        self.channel = channel
        
    def emit(self, record):
        
        log_entry = self.format(record)
        response = self.bot_client.chat_postMessage(
            channel = self.channel,
            text = log_entry,
            as_user = True)
        
        assert response["ok"]
        # assert response["message"]["text"] == log_entry

# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':
    
    # create slackhandler
    slack_handler = SlackHandler(channel = CHANNEL)
    logger.addHandler(slack_handler)
    
    url = 'https://www.moviesinconcert.nl/index.php?page=concertlist'
    html = requests.get(url).content
    df_list = pd.read_html(html)
    all_concerts = df_list[-1]
    
    # make first row the column header
    all_concerts.columns = all_concerts.iloc[0]
    # drop first row used for headers
    all_concerts = all_concerts.drop(all_concerts.index[0])
    
    # find concert in dataframe
    my_mask = all_concerts['Title'].str.contains(TO_FIND, regex = True, case = False)
    my_concerts = all_concerts[my_mask]
    
    for _, row in my_concerts.iterrows():
        # warn on slack
        logger.warning('{} will be performed in {} ({}) on {}'.format(
            row['Title'], row['City'], row['Country'], row['Date']))
        
    if my_concerts.empty:
        logger.warning('Did not find any {} concerts'.format(TO_FIND))
