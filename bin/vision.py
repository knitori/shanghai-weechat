#!/usr/bin/env python3

import sys
import requests
import tempfile
import base64
from urllib.parse import urljoin
from enum import Enum

# options
APIKEY = 'AIzaSyAbLXWXYUsFVT40-VyRkEvbt8MTWXCTjxk'
REFERER = 'https://chireiden.net/J5GmmljZRJC6EOTVXLf5wWl4cOHyGDNiu1Sb3VN7Ekd3GFGxtT'
MAX_LENGTH = 3<<20


def api(url):
    return urljoin('https://vision.googleapis.com/', url)


def main(image_url):
    data = {
        'requests': [{
            'image': {
                'source': {'imageUri': image_url},
            },
            'features': [
                {'type': 'LABEL_DETECTION', 'maxResults': 10},
            ],
        }]
    }

    r = requests.post(
        api('/v1/images:annotate'),
        json=data,
        params={'key': APIKEY},
        headers={'Referer': REFERER}
    )
    if r.status_code == 200:
        data = r.json()
        if len(data['responses']) == 1:
            if 'error' in data['responses'][0]:
                print(data['responses'][0]['error']['message'])
                sys.exit(1)

        tags = []
        for response in data['responses']:
            for annotation in response['labelAnnotations']:
                tags.append('{} ({:.1f}%)'.format(annotation['description'], annotation['score'] * 100))
        print(', '.join(tags))
        return

    print('Unsupported response code from Vision API:', r.status_code)
    sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1])

