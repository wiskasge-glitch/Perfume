import asyncio

from app.scraper.browser import BrowserManager
from app.scraper.fetcher import PageFetcher
from app.scraper.search import SearchBuilder


async def main():

    browser = BrowserManager()

    await browser.start()

    page = await browser.new_page()

    url = (
        SearchBuilder()
        .keyword("versace eros")
        .build()
    )

    html = await PageFetcher().fetch(page, url)

    with open(
        "data/mercadolibre.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    await browser.close()


asyncio.run(main())