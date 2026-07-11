from playwright.async_api import Page

from app.utils.logger import logger


class PageFetcher:

    async def fetch(self, page: Page, url: str) -> str:
        """
        Navega a una URL y devuelve el HTML.
        """

        logger.info(f"Navegando a: {url}")

        await page.goto(
            url,
            wait_until="domcontentloaded"
        )

        html = await page.content()

        logger.info("HTML obtenido correctamente.")

        return html
        