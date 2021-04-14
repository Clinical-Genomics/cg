import random
from typing import Optional

import petname
import requests
from simple_image_download import simple_image_download as simp

RANDOMIZING_WORDS = ["cute", "cuddly", "small", "pet"]

response = simp.simple_image_download


class Avatar:
    @staticmethod
    def get_avatar_url(internal_id: str, tries: int = 25) -> Optional[bool]:

        adjective, animal = Avatar._split_petname(internal_id)
        seed = random.choice(RANDOMIZING_WORDS)
        keywords = f"{seed} {adjective} {animal} icon animal"
        try:
            urls = response().urls(
                keywords=keywords,
                limit=tries,
                extensions={".gif", ".jpg", ".jpeg", ".png", ".tiff"},
            )
        except TypeError:
            urls = response().urls(
                keywords=keywords,
                limit=tries,
            )
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
