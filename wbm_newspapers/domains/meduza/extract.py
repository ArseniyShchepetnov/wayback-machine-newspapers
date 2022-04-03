"""Extract from meduza site."""
import datetime
import re
from typing import List, Optional
from bs4 import BeautifulSoup

from wbm_newspapers.extaction.extraction import BaseExtractor
from wbm_newspapers.extaction.utils import text_tags_class_pattern


class MeduzaExtractor(BaseExtractor):
    """Meduza extractor."""

    def __init__(self, soup: BeautifulSoup, url: str):
        super().__init__(soup, url)

        self.extractor: BaseExtractor

        if self.is_feature(url):
            self.extractor = MeduzaExtractorFeature(soup, url)
        elif self.is_cards(url):
            self.extractor = MeduzaExtractorCards(soup, url)
        elif self.is_short(url):
            self.extractor = MeduzaExtractorShort(soup, url)
        elif self.is_news(url):
            self.extractor = MeduzaExtractorNews(soup, url)
        elif self.is_shapito(url):
            self.extractor = MeduzaExtractorShapito(soup, url)
        elif self.is_slides(url):
            self.extractor = MeduzaExtractorSlides(soup, url)
        else:
            raise ValueError(f"No extractor for '{url}'")

    @staticmethod
    def generate_pattern(name: str) -> re.Pattern:
        """Generates pattern for meduza section detection."""
        pat = (r"(?:https://|http://){0,1}(?:www.){0,1}meduza.io/"
               + name
               + r"/.*")
        return re.compile(pat)

    def is_short(self, url: str) -> bool:
        """Check url is 'short' section."""
        matching = self.generate_pattern("short").fullmatch(url)
        return matching is not None

    def is_cards(self, url: str) -> bool:
        """Check url is 'cards' section."""
        matching = self.generate_pattern("cards").fullmatch(url)
        return matching is not None

    def is_feature(self, url: str) -> bool:
        """Check url is 'feature' section."""
        matching = self.generate_pattern("feature").fullmatch(url)
        return matching is not None

    def is_news(self, url: str) -> bool:
        """Check url is 'news' section."""
        matching = self.generate_pattern("news").fullmatch(url)
        return matching is not None

    def is_shapito(self, url: str) -> bool:
        """Check url is 'shapito' section."""
        matching = self.generate_pattern("shapito").fullmatch(url)
        return matching is not None

    def is_slides(self, url: str) -> bool:
        """Check url is 'slides' section."""
        matching = self.generate_pattern("slides").fullmatch(url)
        return matching is not None

    def get_text(self) -> str:
        """Get text."""
        return self.extractor.get_text()

    def get_title(self) -> str:
        """Get title."""
        return self.extractor.get_title()

    def get_authors(self) -> List[str]:
        """Get authors."""
        return self.extractor.get_authors()

    def get_datetime(self) -> Optional[datetime.datetime]:
        """Get datetime."""
        return self.extractor.get_datetime()

    def get_header_datetime(self) -> str:
        """Get datetime from header."""
        return self.extractor.get_header_datetime()


class MeduzaExtractorSlides(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "(SimpleBlock|QuoteBlock).*",
                                       ["p", "h3", "div"])

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup, "RichTitle.*", "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


class MeduzaExtractorShapito(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "(SimpleBlock|QuoteBlock).*",
                                       ["p", "h3", "div"])

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "(RichTitle|SimpleTitle).*",
                                       "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


class MeduzaExtractorNews(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "(SimpleBlock|QuoteBlock).*",
                                       ["p", "h3", "div"])

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup, "RichTitle.*", "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


class MeduzaExtractorFeature(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "(SimpleBlock|QuoteBlock).*",
                                       ["p", "h3", "div"])

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup, "RichTitle.*", "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


class MeduzaExtractorShort(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup, "MediaCaption.*", "div")

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup, "RichTitle.*", "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


class MeduzaExtractorCards(BaseExtractor):
    """Extract from meduza cards."""

    def get_text(self) -> str:
        return text_tags_class_pattern(self.soup, "CardMaterial-card", "div")

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup, "RichTitle.*", "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime.datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup, "Timestamp.*", "time")


def get_url_date_iso(url: str) -> Optional[datetime.datetime]:
    """Try to get ISO date from URL."""
    result = None
    match = re.search(r"/\d{4}/\d{2}/\d{2}/", url)
    if match is not None:
        data = match.group()
        result = datetime.datetime.strptime(data, r'/%Y/%m/%d/')
    return result
