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


def file_output(output_filename, logger, channel, df):
    """sumary_line

    Keyword arguments:
    argument -- description
    Return: return_description
    """

    logger.info('Compiling all articles into Excel file')
    datestamp = datetime.today().strftime('%Y%m%dT%H%M')
    filename = f'{output_filename}_{channel}_{datestamp}.xlsx'
    df.to_excel(f'{filename}', index=False, encoding='utf-8')
    logger.info(f'{filename} created')


def get_data(urls, base_url):
    scraperapi_key = os.getenv('scraperapi_key')

    article_uuids = []
    for url in urls: 
        params = {'api_key': scraperapi_key, 'url': url}
        response = requests.get('http://api.scraperapi.com/', params=urlencode(params))
        article_uuids.extend([i['uuid'] for i in response.json()['articles']])

    article_urls = [f'{base_url}{i}' for i in article_uuids]    
    article_list = []
    for article_url in article_urls:
        sleep(random.randint(1, 5))
        params = {'api_key': scraperapi_key, 'url': url}
        response = requests.get('http://api.scraperapi.com/', params=urlencode(params))
        article_list.append(response.json())

    return article_list






def main(sources, output_filename, database, table):
    logger = log()

    list_of_urls = ['https://www.fiercebiotech.com/api/v1/fronts/3961?page=1']

    article_uuids = []
    for url in list_of_urls: 
        params = {'api_key': scraperapi_key, 'url': url}
        response = requests.get('http://api.scraperapi.com/', params=urlencode(params))
        print(response.text)

        article_uuids.extend([i['uuid'] for i in response.json()['articles']])



    df = pd.DataFrame(article_list)
    df.channel = df.channel.str.lower()
    df.title = df.title.str.lower()
    df.link = df.link.str.lower()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d/%Y')
    df = df[['date', 'source', 'channel', 'title', 'link']]
    df.drop_duplicates(inplace=True)

    file_output(output_filename, logger, channel, df)
    database_output(logger, df, database, table)


if __name__ == '__main__':

    list_of_urls = ['https://www.fiercebiotech.com/api/v1/fronts/3961?page=1',
                    'https://www.fiercebiotech.com/api/v1/fronts/3961?page=2']

    # num_of_pages = 3
    sources = [{
        'base_url': 'https://www.fiercebiotech.com',
        'url': 'https://www.fiercebiotech.com',
        'channel': None,
        'pages': num_of_pages,
        'source': 'fiercebiotech'
    }
    ]

    main(sources=sources, output_filename='FierceBiotech_Articles',
         database='db', table='fiercebiotech_articles')

    # freq = 100
    # dur = 50
    
    # # loop iterates 5 times i.e, 5 beeps will be produced.
    # for i in range(0, 5):    
    #     winsound.Beep(freq, dur)    
    #     freq+= 100
    #     dur+= 50