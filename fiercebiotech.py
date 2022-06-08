import logging
import os
import pandas as pd
import random
import requests
import sqlite3
import winsound

from datetime import datetime
from dotenv import load_dotenv, dotenv_values
from sqlalchemy import create_engine
from time import sleep
from urllib.parse import urlencode

load_dotenv()


def log():
    """sumary_line

    Keyword arguments:
    argument -- description
    Return: return_description
    """

    logging.basicConfig(format='%(levelname)s | %(asctime)s | %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger


def database_output(logger, df, database, table):
    """sumary_line

    Keyword arguments:
    argument -- description
    Return: return_description
    """

    logger.info('Database set up')
    engine = create_engine(f'sqlite:///{database}.sqlite', echo=False)
    con = engine.connect()
    logger.info(f'Connected to database {engine} - {con}')
    df.to_sql(table, con, index=False, if_exists='append')
    logger.info(f'Appending data to table {table}')
    logger.info('Closing database connection')
    con.close()


def file_output(output_filename, logger, df):
    """sumary_line

    Keyword arguments:
    argument -- description
    Return: return_description
    """
    logger.info('Compiling all articles into Excel file')
    datestamp = datetime.today().strftime('%Y%m%dT%H%M')
    filename = f'{output_filename}_{datestamp}.xlsx'
    df.to_excel(f'{filename}', index=False, encoding='utf-8')
    logger.info(f'{filename} created')


def get_data(urls, base_url):
    logger = log()
    
    scraperapi_key = os.getenv('scraperapi_key')

    logger.info('Getting article uuids')
    article_uuids = []
    for url in urls: 
        params = {'api_key': scraperapi_key, 'url': url}
        response = requests.get('http://api.scraperapi.com/', params=urlencode(params))
        article_uuids.extend([i['uuid'] for i in response.json()['articles']])

    logger.info('Getting article urls')
    article_urls = [f'{base_url}/jsonapi/node/article/{i}' for i in article_uuids]

    logger.info('Getting articles')
    article_list = []
    for article_url in article_urls:
        # sleep(random.randint(1, 5))
        params = {'api_key': scraperapi_key, 'url': article_url}
        response = requests.get('http://api.scraperapi.com/', params=urlencode(params))
        article_list.append(response.json())
    return article_list


if __name__ == '__main__':
    logger = log()

    base_url = 'https://www.fiercebiotech.com'
    urls = ['https://www.fiercebiotech.com/api/v1/fronts/3961?page=1',
            'https://www.fiercebiotech.com/api/v1/fronts/3961?page=2',
            'https://www.fiercebiotech.com/api/v1/fronts/3961?page=3',
            'https://www.fiercebiotech.com/api/v1/fronts/3961?page=4']

    logger.info('Getting data')
    article_list = get_data(urls, base_url)

    logger.info('Parsing articles')
    articles = []
    for article in article_list:
        date = article['data']['attributes']['created'].split('T')[0]
        source = base_url
        channel = article['data']['attributes']['path']['alias'].split('/')[1].strip()
        title = article['data']['attributes']['title']
        link = f"{base_url}{article['data']['attributes']['path']['alias']}"

        data = {
                'date': date,
                'source': source,
                'channel': channel,
                'title': title,
                'link': link
                }
            
        articles.append(data)

    df = pd.DataFrame(articles)
    df.channel = df.channel.str.lower()
    df.title = df.title.str.lower()
    df.link = df.link.str.lower()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d/%Y')
    df = df[['date', 'source', 'channel', 'title', 'link']]
    df.drop_duplicates(inplace=True)

    output_filename = 'FierceBiotech_Articles'
    database = 'db'
    table = 'fiercebiotech_articles'

    file_output(output_filename, logger, df)
    database_output(logger, df, database, table)

    freq = 100
    dur = 50
    
    # loop iterates 5 times i.e, 5 beeps will be produced.
    for i in range(0, 5):    
        winsound.Beep(freq, dur)    
        freq+= 100
        dur+= 50