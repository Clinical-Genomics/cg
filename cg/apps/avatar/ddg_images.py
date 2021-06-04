import requests
import re
import json
import time
import logging


class DdgImages:
    def __init__(self):
        pass

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    def search(self, keywords, max_results=None):
        url = 'https://duckduckgo.com/'
        params = {
            'q': keywords
        }

        print("Hitting DuckDuckGo for Token")

        #   First make a request to above URL, and parse out the 'vqd'
        #   This is a special token, which should be used in the subsequent request
        res = requests.post(url, data=params)
        searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M | re.I)

        if not searchObj:
            print("Token Parsing Failed !")
            return -1

        print("Obtained Token")

        headers = {
            'authority': 'duckduckgo.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'sec-fetch-dest': 'empty',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'referer': 'https://duckduckgo.com/',
            'accept-language': 'en-US,en;q=0.9',
        }

        # https://duckduckgo.com/?
        # q=+mouse&
        # t=hc&
        # va=u&
        # iar=images&
        # iaf=license%3APublic%2Clayout%3ASquare%2Csize%3ASmall%2Ctype%3Atransparent&
        # iax=images&
        # ia=images
        params = (
            ('l', 'us-en'),
            ('o', 'json'),
            ('q', keywords),
            ('vqd', searchObj.group(1)),
            ('f', ',,,'),
            ('p', '1'),
            ('tc', 'hc'),
            ('va', 'u'),
            ('iar', 'images'),
            ('iaf', 'license%3APublic%2Clayout%3ASquare%2Csize%3ASmall%2Ctype%3Atransparent'),
            # ('license', 'ModifyCommercially'),
            # ('color', 'transparent'),
            # ('size', 'Small'),
            # ('layout', 'Square'),
            ('iax', 'images'),
            ('ia', 'images')
        )

        requestUrl = url + "i.js"

        print("Hitting Url : %s", requestUrl)

        while True:
            while True:
                try:
                    res = requests.get(requestUrl, headers=headers, params=params)
                    data = json.loads(res.text)
                    break
                except ValueError as e:
                    print("Hitting Url Failure - Sleep and Retry: %s", requestUrl)
                    time.sleep(5)
                    continue

            print("Hitting Url Success : %s", requestUrl)
            self.printJson(data["results"])

            if "next" not in data:
                print("No Next Page - Exiting")
                exit(0)

            requestUrl = url + data["next"]

    def printJson(self, objs):
        for obj in objs:
            print(
                "Width {0}, Height {1}".format(obj["width"], obj["height"]))
            print(
                "Thumbnail {0}".format(obj["thumbnail"]))
            print(
                "Url {0}".format(obj["url"]))
            print("Title {0}".format(obj["title"].encode('utf-8')))

            print("Image {0}".format(obj["image"]))

            print("__________")
