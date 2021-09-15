"""Command line tool."""
import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


def main():

    args = parse_args()

    config = {
        'domains': args.domains,
    }

    settings = Settings({
        # 'USER_AGENT': (
        #     'Wayback Machine Scraper/{0} '
        #     '(+https://github.com/sangaline/scrapy-wayback-machine)'
        # ).format(get_distribution('wayback-machine-scraper').version),
        'LOG_LEVEL': 'DEBUG' if args.verbose else 'INFO',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_wayback_machine.WaybackMachineMiddleware': 5,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_DEBUG': args.verbose,
        'AUTOTHROTTLE_START_DELAY': 1,
        # 'AUTOTHROTTLE_TARGET_CONCURRENCY': args.concurrency,
        # 'WAYBACK_MACHINE_TIME_RANGE': (getattr(args, 'from'), args.to),
    })

    process = CrawlerProcess(settings)
    # process.crawl(MirrorSpider, **config)
    process.start()


def parse_args():

    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter, description=(
        'Mirror all Wayback Machine snapshots of one or more domains '
        'within a specified time range.'
    ))

    parser.add_argument('domains', metavar='DOMAIN', nargs='+', help=(
        'Specify the domain(s) to scrape. '
        'Can also be a full URL to specify starting points for the crawler.'
    ))

    parser.add_argument('-v', '--verbose', action='store_true', help=(
        'Turn on debug logging.'
    ))

    return parser.parse_args()
