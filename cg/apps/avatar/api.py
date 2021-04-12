import random
import urllib

import petname
from flask_admin.form import thumbgen_filename
from simple_image_download import simple_image_download as simp

RANDOMIZING_WORDS = ['cute', 'cuddly', 'small', 'pet']

response = simp.simple_image_download


class Avatar:
    @staticmethod
    def get_avatar_url(internal_id):

        adjective, animal = Avatar._split_petname(internal_id)
        seed = random.choice(RANDOMIZING_WORDS)
        urls = response().urls(keywords=f"{seed} {adjective} {animal} animal", limit=25, extensions={'.gif', '.jpg', '.jpeg', '.png', '.tiff'})
        random.shuffle(urls)
        for url in urls:
            thumb_url = thumbgen_filename(url)
            if Avatar._is_url_image(thumb_url):
                return thumb_url

        return None

    @staticmethod
    def _is_url_image(image_url):
        from PIL import Image
        try:
            img = Image.open(urllib.request.urlopen(image_url))
            width, height = img.size

            if 0 < width and 0 < height:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def _split_petname(cls, merged_name):

        found_adj = ""
        for adjective in petname.adjectives:
            if adjective in merged_name:
                found_adj = adjective
        found_pet = ""
        for pet in petname.names:
            if pet in merged_name:
                found_pet = pet

        return found_adj, found_pet
