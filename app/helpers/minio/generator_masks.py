from datetime import datetime
from typing import Optional


def format_masks(text, date: Optional[datetime] = None) -> str:
    """
    :param text: текст
    :param date: дата
    masks:
        YYYY    -  год         2000
        YY      -  год         20
        MM      -  месяц       01
        DD      -  день        01
        HH      -  час         01
        mm      -  минуты      59
        MONTH   -  месяц       September
    """
    date = date or datetime.now()
    dates = {
        "DD": date.strftime("%d").zfill(2),
        "MM": date.strftime("%m").zfill(2),
        "YY": date.strftime("%y").zfill(2),
        "HH": date.strftime("%H").zfill(2),
        "mm": date.strftime("%M").zfill(2),
        "YYYY": date.strftime("%Y"),
        "MONTH": date.strftime("%B"),
    }
    return text.format(**dates)
