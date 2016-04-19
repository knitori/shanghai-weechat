#!/usr/bin/env python3

from functools import partial
from urllib.parse import quote
import json
import sys

import requests
from bs4 import BeautifulSoup, Tag
BeautifulSoup = partial(BeautifulSoup, features='lxml')


types_map = {
    'No-adjective': 'No-adj',
    'Na-adjective': 'Na-adj',
    'I-adjective': 'I-adj',
    'Wikipedia definition': 'Wiki',
    # 'Irregular ru verb, plain form ends with -ri': 'Irreg. ru verb with -ri',
    'intransitive verb': 'intr. verb'
}


def main(term):
    url = 'http://jisho.org/api/v1/search/words'
    # test_term = '蟻'
    response = requests.get(url, params=dict(keyword=term))
    obj = response.json()
    if obj['meta']['status'] != 200:
        print('Sorry, some error occured (Status: {})'
              .format(obj['meta']['status']))
        return
    data = obj['data']

    byte_length = 0
    lineparts = []
    if not data:
        print('Sorry, no results found.')
        return

    for entry in data:
        parts = []

        readings = []
        for japanese in entry['japanese']:
            read_parts = []
            word = japanese.get('word', '')
            reading = japanese.get('reading', '')
            if word:
                read_parts.append(word)
            if reading:
                if word:
                    read_parts.append('({})'.format(reading))
                else:
                    read_parts.append(reading)
            if read_parts:
                readings.append(' '.join(read_parts))

        if len(readings) > 4:
            readings = readings[:4]
            readings.append('…')
        parts.append(', '.join(readings))

        for num, sense in enumerate(entry['senses']):
            if num == 3:
                parts.append('/')
                parts.append('…')
                break
            engdefs = sense.get('english_definitions', [])
            if len(engdefs) > 3:
                engdefs = engdefs[:3]
                engdefs.append('…')
            english = ', '.join(engdefs)
            types = sense.get('parts_of_speech', '')
            if english or types:
                parts.append('/')
            if False and types:
                for i, type in enumerate(types):
                    types[i] = types_map.get(type, type)
                parts.append('[{}]'.format(', '.join(types)))
            if english:
                parts.append(english)

        if parts:
            joined_parts = ' '.join(parts)
            if byte_length + 3 + len(joined_parts.encode('utf-8')) >= 400:
                break
            lineparts.append(joined_parts)
            byte_length += 3 + len(joined_parts.encode('utf-8'))

    print(' | '.join(lineparts))
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1])
