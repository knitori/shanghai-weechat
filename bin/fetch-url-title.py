#!/usr/bin/env python3

import os
import sys
from functools import partial
import logging

import urlfetcher
import bs4

bs4.BeautifulSoup = partial(bs4.BeautifulSoup, features='lxml')

FORMAT = '[%(asctime)-15s] %(message)s'
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    filemode='a',
    filename=os.path.expanduser('~/.logs/urlfetcher.log'))


if __name__ == '__main__':
    url = sys.argv[1]
    logging.info('Retrieving url {}'.format(url))
    try:
        result = urlfetcher.fetcher.fetch(url)
    except Exception as e:
        logging.exception(e)
    else:
        if result is not None:
            print(result)
