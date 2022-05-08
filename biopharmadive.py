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
    # options.add_argument('-headless')
    driver = webdriver.Firefox(service=service, options=options)
    for item in sources:
        base_url = item['base_url']
        print(base_url)
        url = item['url']
        channel = item['channel']
        pages = item['pages']
        print(pages)
        source = item['source']
        
    logger.info('Getting list of pages and adding to URL list')
    urls = [f'{base_url}/?page={page}' for page in range(1, pages)]
    logger.info(urls)

        
    article_list = []
    for url in urls:
        logger.info(f'Opening {url}')
        logger.info(f'Begin parse page')
        driver.get(url)
        sleep(15)
        body = driver.page_source
        html = HTML(html=body)

        articles = html.find('.row.feed__item')

        logger.info('Getting articles and appending to list')
        sleep(random.randint(2, 5))
        for article in articles:
            try:
                channel = article.find('.topic-tag', first=True).text
                title = article.find('.feed__title.feed__title--display', first=True).text
                link = base_url + article.find('.feed__title.feed__title--display', first=True).links.pop()

                driver.get(link)
                sleep(random.randint(2, 5))
                body = driver.page_source
                html = HTML(html=body)

                try:
                    if html.find('.published-info'):
                        date = html.find('.published-info', first=True).text
                        if 'Published' in date:
                            date = date.replace('Published', '').strip()
                            date = datetime.strptime(
                                date, '%B %d, %Y').strftime('%Y-%m-%d')
                    elif html.find('.title__date'):
                        date = html.find('.title__date', first=True).text
                        if 'Last updated' in date:
                            date = date.replace('Last updated', '').strip()
                            date = datetime.strptime(
                                date, '%B %d, %Y').strftime('%Y-%m-%d')
                        elif 'Updated' in date:
                            date = date.replace('Updated', '').strip()
                            date = datetime.strptime(
                                date, '%B %d, %Y').strftime('%Y-%m-%d')
                except:
                    None

                data = {'date': date,
                        'source': source,
                        'channel': channel,
                        'title': title,
                        'link': link}

                article_list.append(data)
                sleep(random.randint(5, 10))

            except AttributeError:
                None

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

    num_of_pages = 4
    sources = [{
        'base_url': 'https://www.biopharmadive.com',
        'url': 'https://www.biopharmadive.com',
        'channel': None,
        'pages': num_of_pages,
        'source': 'biopharmadive'
        }]

    main(sources=sources, output_filename='BiopharmaDive_Articles',
         database='db', table='biopharmadive_articles')
