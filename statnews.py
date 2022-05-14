import logging
import pandas as pd
import random
import sqlite3
import winsound

from datetime import datetime
from requests_html import HTML
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import *
from sqlalchemy import create_engine
from time import sleep


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


def main(sources, output_filename, database, table):
    """sumary_line

    Keyword arguments:
    argument -- description
    Return: return_description
    """

    logger = log()
    service = Service('geckodriver.exe')
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    driver = webdriver.Firefox(service=service, options=options)

    for item in sources:
        base_url = item['base_url']
        url = item['url']
        channel = item['channel']
        pages = item['pages']
        source = item['source']
    
    urls = []
    for page in range(pages):
        urls.append(f'{url}/page/{page+1}/')

    article_list = []
    for url in urls:
        logger.info(f'Opening {url}')
        driver.get(url)
        sleep(random.randint(5, 10))
        body = driver.page_source
        html = HTML(html=body)

        logger.info(f'Begin parse page {url}')
        articles = html.find('.text-content')
        for article in articles:
            try:
                title = article.find('.post-title > a', first=True).text
                try:
                    channel = article.find('.card-category > .kicker-link-overlay', first=True).text
                except AttributeError:
                    None
                link = article.find('.post-title', first=True).links.pop()
                if article.find('.post-title', first=True).links.pop().split('/')[3] == '2022':
                    year = article.find('.post-title', first=True).links.pop().split('/')[3]
                    month = article.find('.post-title', first=True).links.pop().split('/')[4]
                    day = article.find('.post-title', first=True).links.pop().split('/')[5]
                    date = f'{year}-{month}-{day}'
                elif article.find('.post-title', first=True).links.pop().split('/')[4] == '2022':
                    year = article.find('.post-title', first=True).links.pop().split('/')[4]
                    month = article.find('.post-title', first=True).links.pop().split('/')[5]
                    day = article.find('.post-title', first=True).links.pop().split('/')[6]
                    date = f'{year}-{month}-{day}'
            except (IndexError, AttributeError):
                None

            data = {    
                'date': date,
                'source': source,
                'channel': channel,
                'title': title,
                'link': link
                }

            article_list.append(data)
        sleep(random.randint(5, 10))


    logger.info('Closing browser instance')
    driver.close()

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

    num_of_pages = 10
    sources = [{
        'base_url': 'https://www.statnews.com',
        'url': 'https://www.statnews.com/latest',
        'channel': None,
        'pages': num_of_pages,
        'source': 'statnews'
    }]

    main(sources, 'Statnews_Articles', 'db', 'statnews_articles')

    freq = 100
    dur = 50
    
    # loop iterates 5 times i.e, 5 beeps will be produced.
    for i in range(0, 5):    
        winsound.Beep(freq, dur)    
        freq+= 100
        dur+= 50