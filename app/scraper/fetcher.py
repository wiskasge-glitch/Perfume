from playwright.async_api import Page

from app.exceptions.scraping import AccessVerificationError
from app.utils.logger import logger


class PageFetcher:
    """
    Navega hacia una página y devuelve su HTML.
    """

    async def fetch(self, page: Page, url: str) -> str:
        logger.info(f"Navegando a: {url}")

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
        )

        final_url = page.url

        if "/gz/account-verification" in final_url:
            logger.error(
                "Mercado Libre redirigió la navegación "
                "a una verificación de cuenta."
            )

            raise AccessVerificationError(
                "No fue posible obtener la página de resultados: "
                "Mercado Libre solicitó una verificación de cuenta."
            )

        if response is None:
            raise RuntimeError(
                "El navegador no recibió una respuesta HTTP."
            )

        if response.status >= 400:
            raise RuntimeError(
                f"Mercado Libre respondió con HTTP {response.status}."
            )

        html = await page.content()

        logger.info(
            f"HTML obtenido correctamente desde: {final_url}"
        )

        return html