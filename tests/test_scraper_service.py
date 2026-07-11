import asyncio

from app.services.scraper_service import ScraperService


async def main():

    service = ScraperService()

    tree = await service.search(
        "versace eros"
    )

    print(tree.html[:500])


asyncio.run(main())