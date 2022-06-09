import logging
import pandas as pd
import random
import sqlite3
import winsound

from datetime import datetime
from dateutil import parser
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
    base_url = 'https://www.endpts.com'
    url = 'https://www.endpts.com'
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    sleep(5)

    try:
        # Click the Channels nav link
        logger.info('Clicking channel navigation link')
        sleep(random.randint(5, 10))
        driver.find_element(By.CLASS_NAME, 'epn_menu > ul > li > span').click()

        # Click the channel > all news dropdown link
        logger.info('Clicking news navigation link')
        sleep(random.randint(5, 10))
        driver.find_element(
            By.CLASS_NAME, 'epn_menu > ul > li > ul > li').click()
    except e:
        logger.error('Clicking channel > news navigation link error')
        raise(e)

    body = driver.page_source
    html = HTML(html=body)

    logger.info('Begin getting and parsing pages')
    articles = html.find('.epn_white_box.epn_item')
    article_list = []
    for article in articles:
        title = article.find('h3', first=True).text.replace('\xad', '')
        try:
            channel = article.find('.epn_byline > .epn_channel > a > span',
                        first=True).text
        except AttributeError:
            channel = ''
        source = 'endpoints'

        logger.info('Getting next article page')
        link = article.find('h3 a', first=True).links.pop()
        driver.get(link)
        body = driver.page_source
        html = HTML(html=body)

        date = html.find(
            '.epn_text > .epn_byline > .epn_time', first=True).text
        if 'Updated' in date:
            date = date.split('U')[0]
        # Need to pass tzinfos to avoid UnknownTimeZoneWarning
        date = parser.parse(date, tzinfos={"EDT": -4 * 3600})
        date = date.strftime('%Y-%m-%d')

        data = {
            'date': date,
            'source': 'www.endpoints.com',
            'channel': channel,
            'title': title,
            'link': link}

        article_list.append(data)

        sleep(random.randint(5, 10))

    df = pd.DataFrame(article_list)
    df.channel = df.channel.str.lower()
    df.title = df.title.str.lower()
    df.link = df.link.str.lower()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d/%Y')
    df = df[['date', 'source', 'channel', 'title', 'link']]
    df.drop_duplicates(inplace=True)

    file_output(output_filename, logger, channel, df)
    database_output(logger, df, database, table)

    logger.info('Closing browser instance')
    driver.close()


if __name__ == '__main__':

    num_of_pages = 1
    sources = [{
        'base_url': 'https://www.endpts.com',
        'url': 'https://www.endpts.com',
        'channel': None,
        'pages': num_of_pages,
        'source': 'endpoints'
    }]

    main(sources, 'Endpoints_Articles', 'db', 'endpoints_articles')
 
    freq = 100
    dur = 50
    
    # loop iterates 5 times i.e, 5 beeps will be produced.
    for i in range(0, 5):    
        winsound.Beep(freq, dur)    
        freq+= 100
        dur+= 50
