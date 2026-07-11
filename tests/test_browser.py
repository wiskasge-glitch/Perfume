import asyncio

from app.scraper.browser import BrowserManager


async def main():

    browser = BrowserManager()

    await browser.start()

    page = await browser.new_page()

    await page.goto("https://www.google.com")

    print(await page.title())

    await browser.close()


asyncio.run(main())