from typing import Optional


class TitleDateTime:

    def __init__(self,
                 minute: int,
                 hour: int,
                 day: Optional[int] = None,
                 month: Optional[int] = None,
                 year: Optional[int] = None):

        self.minute = minute
        self.hour = hour
        self.day = day
        self.month = month
        self.year = year
