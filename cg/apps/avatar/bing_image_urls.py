r"""
bing_image_urls
based on https://github.com/ffreemt/bing-image-urls/blob/master/bing_image_urls/bing_image_urls.py
"""
import logging
from typing import Iterator, List, Union  # , Optional

import asyncio
import imghdr
import re
import httpx

LOG = logging.getLogger(__name__)


# fmt: off
def bing_image_urls(  # pylint: disable=too-many-locals
        query: str,
        page_counter: int = 0,
        limit: int = 5,
        adult_filter_off: bool = False,
        verify_status_only: bool = None,
        filters: str = "",
) -> List[str]:
    # fmt: on
    """ fetch bing image links.
    verify_status_only:
        None (default): no check at all
        True: check status_code == 20
        False: check imghrd.what(None, content) == jpeg|png|etc
    based on https://github.com/gurugaurav/bing_image_downloader/blob/master/bing_image_downloader/bing.py
    query = "bear"
    """
    try:
        count = int(limit)
    except TypeError:
        count = 20

    adult = "on"
    if adult_filter_off:
        adult = "off"

    data = {
        "q": query,
        "first": page_counter,
        "count": count,
        "adlt": adult,
        "qft": filters,
    }

    url = "https://www.bing.com/images/async"

    try:
        resp = httpx.get(url, params=data)
        resp.raise_for_status()
    except Exception as exc:
        LOG.error(exc)
        raise exc

    try:
        links = re.findall(r"murl&quot;:&quot;(.*?)&quot;", resp.text)
    except Exception as exc:
        LOG.error(exc)
        raise exc

    if verify_status_only is None:  # do not check at all
        return links

    loop = asyncio.get_event_loop()

    if verify_status_only:  # status_only
        verified = [*loop.run_until_complete(verify_status(links))]
    else:  # verify imghdr
        verified = loop.run_until_complete(verify_links(links))

    return [elm for idx, elm in enumerate(links) if verified[idx]]


async def verify_status(links: List[str]) -> Union[Iterator[bool], List[bool]]:
    """ verify status_code. """
    async with httpx.AsyncClient() as sess:
        coros = (sess.head(link) for link in links)
        res = await asyncio.gather(*coros)

        def check_status_code(elm):
            if elm.status_code not in (200,):
                return False
            return True
    return map(check_status_code, res)


async def verify_links(links: List[str]) -> List[bool]:
    """ verify link hosts image content.
    res = httpx.get(link)
    return
        True: if imghdr.what(None, res.content) return "jpeg|png|etc.
        False: if imghdr.what(None, res.content) return None or res == None
    """
    async with httpx.AsyncClient() as sess:

        futs = (asyncio.ensure_future(sess.get(link)) for link in links)

        res = []
        for fut in asyncio.as_completed([*futs], timeout=120):
            try:
                res.append(await fut)
            except Exception:
                res.append(None)

        _ = [imghdr.what(None, elm.content) if elm is not None else elm for elm in res]
    # await sess.aclose()

    return [bool(elm) for elm in _]
