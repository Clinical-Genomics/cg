from datetime import datetime


def parse_date(date_string: str) -> datetime:
    if len(date_string) == 6:
        return datetime.strptime(date_string, "%y%m%d")
    elif len(date_string) == 8:
        return datetime.strptime(date_string, "%Y%m%d")
    else:
        raise ValueError("Date format not recognized")
