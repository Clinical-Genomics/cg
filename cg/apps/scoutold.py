# -*- coding: utf-8 -*-
from functools import partial

from .scoutprod import connect as scout_connect, get_reruns


connect = partial(scout_connect, app_key='scoutold')
get_reruns = get_reruns
