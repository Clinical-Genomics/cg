import random
import secrets
from typing import Optional

import petname
import requests
from cg.apps.avatar.bing_image_urls import bing_image_urls


class Avatar:
    @staticmethod
    def get_avatar_url(internal_id: str) -> Optional[bool]:

        urls = None
        adjective, animal = Avatar._split_petname(internal_id)
        filter_array = ["+filterui:license-L2_L3", "+filterui:photo-transparent", "+filterui:aspect-square", "+filterui:imagesize-small"]

        try_cnt = 0
        filters = "".join(filter_array)
        while not urls and filters:
            print(filters)
            query = f"{adjective} {animal}"
            urls = bing_image_urls(
                query=query,
                filters=filters,
                verify_status_only=False,
            )
            if not urls:
                query = f"{animal}"
                urls = bing_image_urls(
                    query=query,
                    filters=filters,
                    verify_status_only=False,
                )

            try_cnt += 1
            filters = "".join(filter_array[:len(filter_array) - try_cnt])

        random.shuffle(urls)
        for url in urls:
            if Avatar.is_url_image(url):
                return url

        return None

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
        for adjective in petname.adjectives:
            if adjective in merged_name:
                found_adj = adjective
        found_pet = ""
        for pet in petname.names:
            if pet in merged_name:
                found_pet = pet

        return found_adj, found_pet
