#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from __future__ import print_function

import socket
orig_getaddrinfo = socket.getaddrinfo


def getaddrinfo_wrap(host, port, family=0, socktype=0, proto=0, flags=0):
    if family in (0, socket.AF_INET6):
        family = socket.AF_INET
    return orig_getaddrinfo(host, port, family, socktype, proto, flags)

socket.getaddrinfo = getaddrinfo_wrap

import re
import sys
from urllib.parse import urlparse, parse_qs

import requests
import bs4

from functools import partial
bs4.BeautifulSoup = partial(bs4.BeautifulSoup, features='lxml')


MAX_URL_LENGTH = 128


def debug(*args):
    print(*args, file=sys.stderr)


def main(search):
    # /search?
    # safe=off
    # &authuser=0
    # &site=webhp
    # &source=hp
    # &q=test
    # &oq=test
    params = {
        'safe': 'off',
        'q': search,
        'oq': search,
        'site': 'webhp',
        'source': 'hp',
    }
    response = requests.get(
        'https://www.google.com/search', params=params)
    
    soup = bs4.BeautifulSoup(response.text)
    h3_list = soup.findAll('h3', class_='r')

    url_list = set()

    calculation = None
    calc = soup.find('div', id='topstuff')
    if calc is not None:
        h2 = calc.find('h2', class_='r')
        if h2 is not None:
            calculation = h2.text

    for h3 in h3_list:
        if h3.a is None:
            continue
        url = urlparse(h3.a['href'])
        query = parse_qs(url.query)

        if 'q' in query and query['q']:
            q_url = query['q'][0]
        elif 'url' in query and query['url']:
            q_url = query['url'][0]

        if '://' in q_url and len(q_url) <= MAX_URL_LENGTH:
            url_list.add(q_url)
            if len(url_list) == 3:
                break

    url_list = list(url_list)

    if calculation:
        url_list.insert(0, calculation)

    if url_list:
        print(' \x02\x0304|\x03\x02 '.join(url_list))
        sys.exit(0)

    sys.exit(2)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        sys.exit(1)
    main(sys.argv[1])
