from app.scraper.browser import BrowserManager
from app.scraper.fetcher import PageFetcher
from app.scraper.parser import Parser
from app.scraper.search import SearchBuilder
from app.utils.logger import logger


class ScraperService:

    def __init__(self):

        self.browser = BrowserManager()
        self.fetcher = PageFetcher()
        self.parser = Parser()

    async def search(self, keyword: str):

        logger.info(f"Buscando: {keyword}")

        url = (
            SearchBuilder()
            .keyword(keyword)
            .build()
        )

        logger.info(f"URL: {url}")

        await self.browser.start()

        page = await self.browser.new_page()

        html = await self.fetcher.fetch(page, url)

        tree = self.parser.parse(html)

        await self.browser.close()

        return tree