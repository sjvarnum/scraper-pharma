import logging
import pandas as pd
import random
import sqlite3

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
        sleep(20)

        article_list = []
        for page in range(1, pages):
            logger.info(f'Begin parse page {page}')
            sleep(random.randint(5, 10))
            logger.info('Checking for pop up')
            try:
                close_popup = driver.find_element(
                    By.CSS_SELECTOR, '.olyticsBandBR')
                logger.info('Pop up found - closing it')
                close_popup.click()
                sleep(random.randint(1, 3))
            except NoSuchElementException:
                logger.info('No pop up detected - continuing')
            try:
                close_newsletter_popup = driver.find_element(
                    By.CSS_SELECTOR, '.fancybox-item')
                logger.info('Pop up found - closing it')
                close_newsletter_popup.click()
                sleep(random.randint(1, 3))
            except NoSuchElementException:
                logger.info('No pop up detected  - continuing')

            body = driver.page_source
            html = HTML(html=body)
            articles = html.find('.article')

            logger.info('Getting articles and appending to list')
            sleep(random.randint(2, 5))
            for article in articles:
                try:
                    title = article.find('.article-title', first=True).text
                except:
                    None
                try:
                    link = f'{base_url}' + \
                        article.find('.article-title', first=True).links.pop()
                except:
                    None
                try:
                    date = article.find('.article-date > time', first=True)
                    date = date.attrs['datetime']
                    date = date.split('T')[0]
                except:
                    None
                try:
                    channel = channel
                except:
                    None

                data = {'date': date,
                        'source': source,
                        'channel': channel,
                        'title': title,
                        'link': link}

                article_list.append(data)

            sleep(random.randint(5, 10))

            try:
                driver.find_element(By.LINK_TEXT, 'Next').click()
            except ElementClickInterceptedException:
                driver.find_element(By.LINK_TEXT, 'Next').click()

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

    num_of_pages = 3
    sources = [{
        'base_url': 'https://www.beckershospitalreview.com',
        'url': 'https://www.beckershospitalreview.com/pharmacy.html',
        'channel': 'pharmacy',
        'pages': num_of_pages,
        'source': 'becker'
    },
        {
        'base_url': 'https://www.beckershospitalreview.com',
        'url': 'https://www.beckershospitalreview.com/legal-regulatory-issues.html',
        'channel': 'legal-regulatory-issues',
        'pages': num_of_pages,
        'source': 'becker'
    },
        {
        'base_url': 'https://www.beckershospitalreview.com',
        'url': 'https://www.beckershospitalreview.com/oncology.html',
        'channel': 'oncology',
        'pages': num_of_pages,
        'source': 'becker'
    },
        {'base_url': 'https://www.beckerspayer.com',
         'url': 'https://www.beckerspayer.com',
         'channel': 'payer',
         'pages': num_of_pages,
         'source': 'becker'
         }
    ]

    main(sources=sources, output_filename='Becker_Articles',
         database='db', table='becker_articles')
