
import logging
import os

import scrapy
from anynews_wbm.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                                     WaybackMachineResponseCDX)

logger = logging.getLogger(__name__)


# class SpiderWaybackMachineCollect(SpiderWaybackMachineBase):
#     """Basic Wayback Machine domain scraper."""

#     name = 'collect'

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self._it = 0

#     def parse_cdx(self, response: scrapy.http.TextResponse):
#         """Parse cdx responses."""

#         data = WaybackMachineResponseCDX.from_text(response.text)

#         logging.info("CDX response %d rows.", data.n_rows)

#         data = self._filter_cdx_response(data)

#         logging.info("CDX response %d rows after filtering.", data.n_rows)

#         data.data.to_pickle(os.path.join(self.scraper_outdir,
#                                          f"{self._it}.pkl.bz2"))

#         if data.resume_key is not None:

#             self._cdx.set_resume_key(show=True, key=data.resume_key)
#             request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

#             self._it += 1

#             yield request

#     def parse(self, response: scrapy.http.TextResponse):  # pylint: disable=arguments-differ
#         pass
