import random
import secrets
from time import sleep
from typing import Optional

import petname
import requests
from bing_image_urls import bing_image_urls


class Avatar:
    @staticmethod
    def get_avatar_url(internal_id: str) -> Optional[bool]:
        for url in Avatar.get_avatar_urls(internal_id):
            if Avatar.is_url_image(url):
                return url

    @staticmethod
    def get_avatar_urls(internal_id: str) -> Optional[bool]:

        urls = None
        adjective, animal = Avatar._split_petname(internal_id)
        filter_array = [
            "+filterui:license-L2_L3",
            "+filterui:aspect-square",
            "+filterui:photo-transparent",
            "+filterui:imagesize-small",
        ]

        try_cnt = 0
        filters = "".join(filter_array)
        while not urls and filters:
            query = f"{animal}"
            urls = bing_image_urls(
                query=query,
                limit=5,
                filters=filters,
                verify_status_only=False,
            )
            if not urls:
                sleep(secrets.SystemRandom().randint(0, max(len(filter_array) - try_cnt, 1)))
            try_cnt += 1
            filters = "".join(filter_array[: len(filter_array) - try_cnt])

        random.shuffle(urls)
        return urls

    @staticmethod
    def is_url_image(image_url: str) -> bool:
        from PIL import Image

        try:
            img = Image.open(requests.get(image_url, stream=True).raw)
            width, height = img.size

            if 0 < width and 0 < height:
                return True
        except Exception:
            return False

        return False

    @classmethod
    def _split_petname(cls, merged_name: str) -> (str, str):

        found_adj = ""
        sorted_adjectives = sorted(petname.adjectives, key=len, reverse=True)
        sorted_pets = sorted(petname.names, key=len, reverse=True)
        for adjective in sorted_adjectives:
            if merged_name.startswith(adjective):
                found_adj = adjective
                break
        found_pet = ""
        for pet in sorted_pets:
            if merged_name.endswith(pet):
                found_pet = pet
                break

        return found_adj, found_pet
