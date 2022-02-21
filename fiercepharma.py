from datetime import datetime
import random
import time

import requests
import pandas as pd

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0'
]
random_user_agent = random.choice(user_agents)

res = []
for page_num in range(1, 5):
    url = f'https://www.fiercepharma.com/api/v1/fronts/node?_format=json&page={page_num}'
    payload = {}
    headers = {'User-Agent': random_user_agent}
    params = {'sponsoredCount': '0',
              'sectionId': '33231',
              'limit': '1'}

    response = requests.get(url, headers=headers, data=payload, params=params)

    data = response.json()
    for article in data['data']:
        res.append(article)

    n = random.randint(1, 5)
    time.sleep(n)

df = pd.json_normalize(res)

df = df[['publishedDate', 'primaryTaxonomy.label', 'title', 'uri']]
df.rename(columns={'publishedDate': 'date',
                   'primaryTaxonomy.label': 'channel',
                   'title': 'title',
                   'uri': 'link'}, inplace=True)
df['source'] = 'www.fiercepharma.com'
df['channel'] = df['channel'].str.lower()
df['title'] = df['title'].str.lower()
df.link = df.link.str.lower()
df = df[['date', 'source', 'channel', 'title', 'link']]
df.drop_duplicates(inplace=True)
datestamp = datetime.today().strftime('%Y%m%dT%H%M')
df.to_csv(f'Fierce_Pharma_Articles_{datestamp}.csv', index=False)
