"""Priority specific constants"""

PRIORITY_MAP = {"research": 0, "standard": 1, "priority": 2, "express": 3, "clinical trials": 4}

REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}

PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())
