#!/usr/bin/env python3

from urllib.parse import urljoin
import requests
import bs4
import json
from functools import partial
bs4.BeautifulSoup = partial(bs4.BeautifulSoup, features='lxml')

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'
headers['Pragma'] = 'no-cache'
headers['Cache-Control'] = 'no-cache'
headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
headers['Accept-Encoding'] = 'gzip, deflate, sdch'


def main():
    base_url = 'http://dynasty-scans.com/'

    while True:
        r = requests.get(base_url, headers=headers)
        soup = bs4.BeautifulSoup(r.text)
        header = soup.find('h4', text='Random Chapter')
        anchor = header.next_sibling.next_sibling
        tags = [span.text for span in
                anchor.find('div', class_='tags').findAll('span')]
        if 'yuri' not in map(str.lower, tags):
            continue
        chapter_link = anchor.get('href', None)
        if chapter_link is None:
            continue

        title = anchor.find('div', class_='title')
        if title is not None:
            title = title.text

        authors = anchor.find('div', class_='authors')
        if authors is not None:
            authors = authors.text

        chapter_link = urljoin(base_url, chapter_link)
        break

    data = {}
    data['link'] = chapter_link
    data['tags'] = tags
    data['title'] = title
    data['authors'] = authors
    print(json.dumps(data, indent=4))


if __name__ == '__main__':
    main()
