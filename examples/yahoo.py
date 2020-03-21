#/usr/bin/python3
# -*- coding:Utf-8 -*-
import re
import sys
import time
import datetime
import requests

def get_cookie_value(r):
    return {'B': r.cookies['B']}

def get_page_data(symbol):
    url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
    r = requests.get(url)
    cookie = get_cookie_value(r)
    lines = r.content.decode('unicode-escape').strip(). replace('}', '\n')
    return cookie, lines.split('\n')

def find_crumb_store(lines):
    # Looking for
    # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
    for l in lines:
        if re.findall(r'CrumbStore', l):
            return l
    print("Did not find CrumbStore")

def split_crumb_store(v):
    return v.split(':')[2].strip('"')

def get_cookie_crumb(symbol):
    cookie, lines = get_page_data(symbol)
    crumb = split_crumb_store(find_crumb_store(lines))
    return cookie, crumb

def get_data(symbol, start_date, end_date, cookie, crumb):
    # interval = 1d, 1wk, 1mo
    # events = history, div, split
    filename = '%s.csv' % (symbol)
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, start_date, end_date, crumb)
    print(url)
    print(cookie)
    response = requests.get(url, cookies=cookie)
    with open (filename, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)

def get_now_epoch():
    # @see https://www.linuxquestions.org/questions/programming-9/python-datetime-to-epoch-4175520007/#post5244109
    return int(time.time())

def get_now_5():
    # @see https://www.linuxquestions.org/questions/programming-9/python-datetime-to-epoch-4175520007/#post5244109
    return int(time.time())

def download_quotes(symbol):
    start_date = get_now_epoch() - (3600 * 24 * 5)
    end_date = get_now_epoch()
    cookie, crumb = get_cookie_crumb(symbol)
    get_data(symbol, start_date, end_date, cookie, crumb)

symbol = "FR0010340620.PA"
#symbol = input('Enter the symbol: ')
print("--------------------------------------------------")
print("Downloading %s to %s.csv" % (symbol, symbol))
download_quotes(symbol)
print("--------------------------------------------------")

"""
https://query1.finance.yahoo.com/v7/finance/download/FR0010340620.PA?period1=0&period2=1516718401&interval=1d&events=history&crumb=Yj35QSp6xsg
https://query1.finance.yahoo.com/v7/finance/download/FR0010340620.PA?period1=0&period2=1516718213&interval=1d&events=history&crumb=qD04iX8mmlC
"""