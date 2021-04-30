"""Parse Wayback Machine response."""
import json
from typing import Optional

import pandas as pd
import requests


class WaybackResponse:
    """Wayback response table."""

    def __init__(self,
                 data: pd.DataFrame,
                 resume_key: Optional[str] = None):

        self._data = data
        self.resume_key = resume_key

    @property
    def data(self) -> pd.DataFrame:
        """Data property."""
        return self._data

    @classmethod
    def from_response(cls, response: requests.Response) -> 'WaybackResponse':
        """Data from json response."""

        json_data = json.loads(response.content.decode("utf-8"))

        columns = json_data[0]

        if len(json_data[-1] == 1) and len(json_data[-2] == 0):

            resume_key = json_data[-1][0]
            data = pd.DataFrame(json_data[1:-2], columns=columns)

        else:
            resume_key = None
            data = pd.DataFrame(json_data[1:], columns=columns)

        return cls(data, resume_key=resume_key)
