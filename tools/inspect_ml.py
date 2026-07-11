import asyncio
import json
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.scraper.browser import BrowserManager
from app.scraper.fetcher import PageFetcher
from app.scraper.search import SearchBuilder
from app.utils.logger import logger


OUTPUT_DIRECTORY = Path("data/inspection")


async def main() -> None:
    """
    Abre una búsqueda de Mercado Libre y guarda:

    - HTML completo.
    - Captura de pantalla.
    - Resumen con posibles selectores.
    """

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    browser = BrowserManager()

    try:
        await browser.start()
        page = await browser.new_page()

        url = (
            SearchBuilder()
            .keyword("versace eros")
            .build()
        )

        fetcher = PageFetcher()
        await fetcher.fetch(page, url)

        # Mercado Libre puede continuar cargando elementos después del HTML inicial.
        try:
            await page.wait_for_load_state(
                "networkidle",
                timeout=8_000,
            )
        except PlaywrightTimeoutError:
            logger.warning(
                "La página siguió haciendo solicitudes, "
                "pero continuaremos con la inspección."
            )

        await page.wait_for_timeout(2_500)

        html = await page.content()
        title = await page.title()
        final_url = page.url

        html_path = OUTPUT_DIRECTORY / "mercadolibre.html"
        screenshot_path = OUTPUT_DIRECTORY / "mercadolibre.png"
        summary_path = OUTPUT_DIRECTORY / "summary.json"

        html_path.write_text(
            html,
            encoding="utf-8",
        )

        await page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        # Posibles selectores usados por diferentes versiones
        # del diseño de Mercado Libre.
        candidate_selectors = [
            "li.ui-search-layout__item",
            ".ui-search-result",
            ".ui-search-result__wrapper",
            ".poly-card",
            "a.poly-component__title",
            "h2.ui-search-item__title",
            ".andes-money-amount__fraction",
            ".poly-component__seller",
        ]

        selector_counts: dict[str, int] = {}

        for selector in candidate_selectors:
            selector_counts[selector] = await page.locator(
                selector
            ).count()

        body_text = ""

        body = page.locator("body")

        if await body.count() > 0:
            body_text = await body.inner_text()

        summary = {
            "title": title,
            "requested_url": url,
            "final_url": final_url,
            "html_characters": len(html),
            "selector_counts": selector_counts,
            "body_preview": body_text[:1_000],
        }

        summary_path.write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

        logger.info(f"Título: {title}")
        logger.info(f"URL final: {final_url}")
        logger.info(f"Tamaño del HTML: {len(html)} caracteres")

        for selector, count in selector_counts.items():
            logger.info(
                f"Selector {selector!r}: {count} coincidencias"
            )

        logger.info(f"HTML guardado en: {html_path}")
        logger.info(f"Captura guardada en: {screenshot_path}")
        logger.info(f"Resumen guardado en: {summary_path}")

    except Exception:
        logger.exception(
            "Ocurrió un error durante la inspección de Mercado Libre."
        )
        raise

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())