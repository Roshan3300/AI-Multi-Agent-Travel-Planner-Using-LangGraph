import os
import requests
from dotenv import load_dotenv
load_dotenv()
print('AVIATIONSTACK_API_KEY set:', os.getenv('AVIATIONSTACK_API_KEY') is not None)
API_KEY = os.getenv('AVIATIONSTACK_API_KEY')
url = 'https://api.aviationstack.com/v1/flights'
params = {'access_key': API_KEY, 'limit': 5, 'query': 'Tokyo'}
print('params', params)
try:
    resp = requests.get(url, params=params, timeout=15)
    print('status', resp.status_code)
    print('headers', resp.headers.get('Content-Type'))
    text = resp.text
    print('text start', text[:300].replace('\n',' '))
    try:
        data = resp.json()
        print('json keys', list(data.keys())[:10])
        print('json sample', data)
    except Exception as e:
        print('json error', type(e).__name__, e)
except Exception as exc:
    print('request failed', exc)

import psycopg
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
print('DATABASE_URL set:', DATABASE_URL is not None, DATABASE_URL)
try:
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('DB test query PASS', cur.fetchone())
    cur.close()
    conn.close()
except Exception as exc:
    print('DB error', type(exc).__name__, exc)
