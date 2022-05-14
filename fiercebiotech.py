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
        logger.info(f'Opening {url}')
        driver.get(url)
        sleep(random.randint(10, 20))

        logger.info(
            'Scroll to bottom of page to find "see more articles" button')
        see_more_link = driver.find_element(By.LINK_TEXT, 'See more articles')
        driver.execute_script(
            'arguments[0].scrollIntoView(true);', see_more_link)
        sleep(5)

        for page in range(1, pages):
            logger.info(f'Begin parse page {page}')
            sleep(random.randint(5, 10))
            logger.info('Checking for pop up')
            try:
                close_button = driver.find_element(
                    By.CSS_SELECTOR, '.close-persistent-bar').click()
                logger.info('Pop up found - closing it')
                sleep(5)
                driver.find_element(By.LINK_TEXT, 'See more articles').click()
            except:
                logger.info('No pop up detected - continuing')
                driver.find_element(By.LINK_TEXT, 'See more articles').click()

            logger.info(
                'Scroll to bottom of page to find "see more articles button"')
            sleep(5)
            see_more_link = driver.find_element(
                By.LINK_TEXT, 'See more articles')
            logger.info('Click the "see more articles button"')
            driver.execute_script(
                'arguments[0].scrollIntoView(true);', see_more_link)
            see_more_link.click()
            sleep(5)
            n = random.randint(1, 5)
            sleep(n)

    body = driver.page_source
    html = HTML(html=body)
    articles = html.find('article.node-listing.prosumer.row')
    article_list = []
    for article in articles:
        try:
            title = article.find('.element-title.small', first=True).text
            # print(title)
        except:
            None
        try:
            link = url[:-1] + \
                article.find('.element-title.small > a',
                             first=True).links.pop()
            # print(link)
        except:
            None
        try:
            date = article.find('span.date.d-inline-block', first=True).text
            date = datetime.strptime(
                date[:-2], '%b %d, %Y %H:%M').strftime('%Y-%m-%d')
            # print(date)
        except:
            None
        try:
            channel = article.find(
                '.label.label-small > span > a', first=True).text
            # print(channel)
        except:
            None

        data = {
            'date': date,
            'source': 'www.fiercebiotech.com',
            'channel': channel,
            'title': title,
            'link': link
        }

        article_list.append(data)

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

    num_of_pages = 3
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

    freq = 100
    dur = 50
    
    # loop iterates 5 times i.e, 5 beeps will be produced.
    for i in range(0, 5):    
        winsound.Beep(freq, dur)    
        freq+= 100
        dur+= 50