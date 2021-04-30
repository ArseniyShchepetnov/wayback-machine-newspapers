"""URL constructor"""
import datetime
from typing import Any, Dict, List, Optional

import requests

CDX_DOCS = 'https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server'


class WaybackMachineCDX:
    """
    CDX request constructor for Wayback Machine.
    """

    base = 'http://web.archive.org/cdx/search/'

    scopes = ['exact', 'prefix', 'host', 'domain']
    output_formats = ['json']
    field_order_items = ["urlkey", "timestamp", "original",
                         "mimetype", "statuscode", "digest", "length"]

    datetime_format = r'%Y%m%d%H%M%S'

    def __init__(self,
                 url: str,
                 **kwargs):
        """
        Parameters
        ----------
        url : str
            Url parameter
        kwargs :
            Other parameters for the CDX query.
        """

        self.url = url

        self.params = {}

        params_map = {
            'matchType': self.set_match_scope,
            'output': self.set_output_format,
            'fl': self.set_field_order,
            'from_dt': lambda x: self.set_datatime_range(x, None),
            'to_dt': lambda x: self.set_datatime_range(None, x),
            'limit': lambda x: self.set_limits(x, None, None),
            'fastLatest': lambda x: self.set_limits(None, x, None),
            'offset': lambda x: self.set_limits(None, None, x),
            'showResumeKey': lambda x: self.set_resume_key(x, None),
            'resumeKey': lambda x: self.set_resume_key(None, x)
        }

        for name, value in kwargs.items():
            params_map[name](value)

    @property
    def cdx(self) -> str:
        """Return constructed CDX query."""
        return self.construct(self.params)

    def construct(self, params: Optional[Dict[str, Any]] = None) -> str:
        """Construct with parameters."""

        result = self.base + f"cdx?url={self.url}"

        if params:
            for param, value in params.items():

                if value is not None:
                    result += f"&{param}={value}"

        return result

    def test_cdx_is_valid(self) -> bool:
        """Check that request with limit=1 parameter returns OK code."""

        params = self.params.copy()

        params['limit'] = 1

        cdx = self.construct(params)

        response = requests.get(cdx)

        return response.status_code == requests.codes.ok  # pylint: disable=maybe-no-member

    def set_match_scope(self, scope: Optional[str] = None):
        """Set scope 'matchType' parameter."""

        if scope is not None and scope not in self.scopes:
            raise ValueError(f"Scope is invalid {scope}. "
                             f"Valid scopes: {self.scopes}. "
                             f"See {CDX_DOCS} for details")

        self.params['matchType'] = scope

    def set_field_order(self, fl: Optional[List[str]] = None):

        if fl is not None:
            unknown_items = list(set(fl) - set(self.field_order_items))
            if len(unknown_items) > 0:
                raise ValueError(f"Unknown items in 'fl': {unknown_items}. "
                                 f"Valid items: {self.field_order_items}. "
                                 f"See {CDX_DOCS} for details")
            fl = ",".join(fl)

        self.params['fl'] = fl

    def set_output_format(self, output: Optional[str] = None):

        if output is not None and output not in self.output_formats:
            raise ValueError(f"Output format is invalid {output}. "
                             f"Valid formats: {self.output_formats}. "
                             f"See {CDX_DOCS} for details")

        self.params['output'] = output

    def set_datatime_range(self,
                           from_dt: Optional[datetime.datetime] = None,
                           to_dt: Optional[datetime.datetime] = None):

        for name, val in zip(['from', 'to'], [from_dt, to_dt]):

            if val is not None:
                val = val.strftime(self.datetime_format)
                self.params[name] = val

    def set_limits(self,
                   limit: Optional[int] = None,
                   fastLatest: Optional[bool] = None,
                   offset: Optional[int] = None):

        self.params['limit'] = limit
        self.params['fastLatest'] = fastLatest
        self.params['offset'] = offset

    def set_resume_key(self,
                       show: Optional[bool] = None,
                       key: Optional[str] = None):

        self.params['showResumeKey'] = show
        self.params['resumeKey'] = key
